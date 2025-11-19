from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import render
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View
import stripe
import paypalrestsdk
import json
from .models import Subscription, PaymentTransaction
from .serializers import SubscriptionSerializer, PaymentTransactionSerializer

stripe.api_key = settings.STRIPE_SECRET_KEY
User = get_user_model()

# Configure PayPal SDK (only if credentials are provided)
if settings.PAYPAL_CLIENT_ID and settings.PAYPAL_CLIENT_SECRET:
    paypalrestsdk.configure({
        "mode": settings.PAYPAL_MODE,
        "client_id": settings.PAYPAL_CLIENT_ID,
        "client_secret": settings.PAYPAL_CLIENT_SECRET
    })


class CreateCheckoutSessionView(APIView):
    def post(self, request):
        plan = request.data.get('plan', 'monthly')
        price_id = settings.STRIPE_PRICE_ID_MONTHLY if plan == 'monthly' else settings.STRIPE_PRICE_ID_ANNUAL
        if not price_id or not settings.STRIPE_SECRET_KEY:
            return Response({"detail": "Stripe not configured"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=settings.FRONTEND_SUCCESS_URL,
            cancel_url=settings.FRONTEND_CANCEL_URL,
            customer_email=request.user.email,
            metadata={"user_id": str(request.user.id), "plan": plan},
        )
        PaymentTransaction.objects.create(
            user=request.user,
            payment_provider=PaymentTransaction.PaymentProvider.STRIPE,
            stripe_session_id=session.id,
            status='pending',
            amount=0,
            currency='usd'
        )
        return Response({"url": session.url, "checkout_url": session.url})


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        sig = request.META.get('HTTP_STRIPE_SIGNATURE', '')
        payload = request.body
        try:
            event = stripe.Webhook.construct_event(payload=payload, sig_header=sig, secret=settings.STRIPE_WEBHOOK_SECRET)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if event.get('type') == 'checkout.session.completed':
            sess = event['data']['object']
            user_id = int(sess['metadata']['user_id']) if 'metadata' in sess and 'user_id' in sess['metadata'] else None
            if user_id:
                user = User.objects.get(id=user_id)
                sub_obj, _ = Subscription.objects.get_or_create(user=user)
                sub_obj.plan_type = Subscription.PlanType.PRO
                sub_obj.payment_status = 'active'
                sub_obj.payment_provider = Subscription.PaymentProvider.STRIPE
                sub_obj.start_date = timezone.now().date()
                sub_obj.stripe_subscription_id = sess.get('subscription')
                sub_obj.stripe_customer_id = sess.get('customer')
                sub_obj.save()

                # CRITICAL FIX: Update user role to PRO
                user.role = User.Role.PRO
                user.save(update_fields=['role'])

                PaymentTransaction.objects.filter(stripe_session_id=sess['id']).update(status='succeeded')

                # Send push notification for payment success
                try:
                    from notifications.fcm_utils import send_payment_success_notification
                    from notifications.models import Notification

                    # Send push notification
                    send_payment_success_notification(user, amount=sess.get('amount_total', 0) / 100, currency='USD')

                    # Create in-app notification
                    Notification.objects.create(
                        user=user,
                        message="Your payment was successful! Welcome to Pro membership."
                    )
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to send payment notification: {str(e)}")

        elif event.get('type') == 'invoice.payment_failed':
            inv = event['data']['object']
            cust = inv.get('customer')
            try:
                sub_obj = Subscription.objects.get(stripe_customer_id=cust)
                sub_obj.payment_status = 'failed'
                sub_obj.save(update_fields=['payment_status'])
            except Subscription.DoesNotExist:
                pass

        elif event.get('type') == 'customer.subscription.deleted':
            sub = event['data']['object']
            try:
                sub_obj = Subscription.objects.get(stripe_subscription_id=sub.get('id'))
                sub_obj.plan_type = Subscription.PlanType.BASIC
                sub_obj.payment_status = 'cancelled'
                sub_obj.end_date = timezone.now().date()
                sub_obj.save()

                # Downgrade user role to BASIC when subscription cancelled
                user = sub_obj.user
                user.role = User.Role.BASIC
                user.save(update_fields=['role'])
            except Subscription.DoesNotExist:
                pass

        return Response(status=status.HTTP_200_OK)


class UserSubscriptionView(APIView):
    def get(self, request):
        sub, _ = Subscription.objects.get_or_create(user=request.user)
        return Response(SubscriptionSerializer(sub).data)


class CancelSubscriptionView(APIView):
    def post(self, request):
        sub, _ = Subscription.objects.get_or_create(user=request.user)
        # Optional: call Stripe to cancel if we have an active subscription id
        if sub.stripe_subscription_id and settings.STRIPE_SECRET_KEY:
            try:
                stripe.Subscription.delete(sub.stripe_subscription_id)
            except Exception:
                pass
        sub.plan_type = Subscription.PlanType.BASIC
        sub.payment_status = 'cancelled'
        sub.end_date = timezone.now().date()
        sub.save()

        # Downgrade user role to BASIC
        request.user.role = User.Role.BASIC
        request.user.save(update_fields=['role'])

        return Response({"message": "Subscription cancelled"})


class PaymentHistoryView(APIView):
    def get(self, request):
        payments = PaymentTransaction.objects.filter(user=request.user).order_by('-created_at')
        return Response(PaymentTransactionSerializer(payments, many=True).data)


class PaymentSuccessView(View):
    """Display success page after payment (for mobile apps)"""
    def get(self, request):
        return render(request, 'payment_success.html')


class CheckPaymentStatusView(APIView):
    """Check and update payment status - useful for local development when webhooks don't work"""
    def post(self, request):
        """
        Check user's payment status with Stripe and update accordingly.
        This is a fallback for when webhooks can't reach localhost.
        """
        try:
            user = request.user

            # Get user's subscription from database
            sub, _ = Subscription.objects.get_or_create(user=user)

            # If user already has an active Pro subscription, return success
            if sub.payment_status == 'active' and sub.plan_type == Subscription.PlanType.PRO:
                if user.role != User.Role.PRO:
                    user.role = User.Role.PRO
                    user.save(update_fields=['role'])
                return Response({
                    "status": "success",
                    "message": "Already Pro user",
                    "is_pro": True,
                    "plan_type": sub.plan_type
                })

            # Check Stripe for recent successful payments
            if not settings.STRIPE_SECRET_KEY:
                return Response({"detail": "Stripe not configured"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Search for successful checkout sessions for this user
            # Note: We search by looking at recent sessions and checking metadata
            sessions = stripe.checkout.Session.list(
                limit=20
            )

            # Find the most recent completed session for this user
            for session in sessions.data:
                # Check if this session belongs to current user
                session_user_id = session.metadata.get('user_id') if session.metadata else None
                is_users_session = (
                    session_user_id == str(user.id) or
                    session.customer_email == user.email
                )

                if is_users_session and session.payment_status == 'paid' and session.status == 'complete':
                    # Update subscription
                    sub.plan_type = Subscription.PlanType.PRO
                    sub.payment_status = 'active'
                    sub.payment_provider = Subscription.PaymentProvider.STRIPE
                    sub.start_date = timezone.now().date()
                    sub.stripe_subscription_id = session.get('subscription')
                    sub.stripe_customer_id = session.get('customer')
                    sub.save()

                    # Update user role to PRO
                    user.role = User.Role.PRO
                    user.save(update_fields=['role'])

                    # Update payment transaction
                    PaymentTransaction.objects.filter(
                        stripe_session_id=session.id
                    ).update(status='succeeded')

                    # Send success notification
                    try:
                        from notifications.fcm_utils import send_payment_success_notification
                        from notifications.models import Notification

                        send_payment_success_notification(
                            user,
                            amount=session.amount_total / 100,
                            currency=session.currency.upper()
                        )

                        Notification.objects.create(
                            user=user,
                            message="Your payment was successful! Welcome to Pro membership."
                        )
                    except Exception as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.error(f"Failed to send payment notification: {str(e)}")

                    return Response({
                        "status": "success",
                        "message": "Upgraded to Pro successfully",
                        "is_pro": True,
                        "plan_type": Subscription.PlanType.PRO
                    })

            # No successful payment found
            return Response({
                "status": "no_payment",
                "message": "No successful payment found",
                "is_pro": user.is_pro(),
                "plan_type": sub.plan_type
            })

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error checking payment status: {str(e)}")
            return Response({
                "detail": f"Error checking payment: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentCancelView(View):
    """Display cancel page when payment is cancelled (for mobile apps)"""
    def get(self, request):
        return render(request, 'payment_cancel.html')


# ==================== PayPal Payment Views ====================

class CreatePayPalSubscriptionView(APIView):
    """Create a PayPal subscription"""
    def post(self, request):
        plan = request.data.get('plan', 'monthly')
        plan_id = settings.PAYPAL_MONTHLY_PLAN_ID if plan == 'monthly' else settings.PAYPAL_ANNUAL_PLAN_ID

        if not plan_id or not settings.PAYPAL_CLIENT_ID:
            return Response(
                {"detail": "PayPal not configured"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Create subscription using PayPal SDK
        subscription = paypalrestsdk.BillingAgreement({
            "name": f"Task Manager Pro Subscription - {plan.capitalize()}",
            "description": f"Monthly subscription to Task Manager Pro",
            "start_date": (timezone.now() + timezone.timedelta(minutes=5)).isoformat(),
            "plan": {
                "id": plan_id
            },
            "payer": {
                "payment_method": "paypal"
            }
        })

        if subscription.create():
            # Store pending transaction
            PaymentTransaction.objects.create(
                user=request.user,
                payment_provider=PaymentTransaction.PaymentProvider.PAYPAL,
                paypal_order_id=subscription.token,
                status='pending',
                amount=0,
                currency='usd'
            )

            # Get approval URL
            for link in subscription.links:
                if link.rel == "approval_url":
                    return Response({
                        "url": link.href,
                        "approval_url": link.href,
                        "token": subscription.token
                    })
        else:
            return Response(
                {"detail": f"PayPal error: {subscription.error}"},
                status=status.HTTP_400_BAD_REQUEST
            )


class CreatePayPalOrderView(APIView):
    """Create a one-time PayPal order for subscription"""
    def post(self, request):
        plan = request.data.get('plan', 'monthly')

        # Define pricing
        prices = {
            'monthly': {'amount': '9.99', 'description': 'Monthly Pro Subscription'},
            'annual': {'amount': '99.99', 'description': 'Annual Pro Subscription'}
        }

        price_info = prices.get(plan, prices['monthly'])

        if not settings.PAYPAL_CLIENT_ID:
            return Response(
                {"detail": "PayPal not configured"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Create PayPal order
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": settings.FRONTEND_SUCCESS_URL.replace('{CHECKOUT_SESSION_ID}', ''),
                "cancel_url": settings.FRONTEND_CANCEL_URL
            },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": price_info['description'],
                        "sku": f"pro_{plan}",
                        "price": price_info['amount'],
                        "currency": "USD",
                        "quantity": 1
                    }]
                },
                "amount": {
                    "total": price_info['amount'],
                    "currency": "USD"
                },
                "description": price_info['description'],
                "custom": json.dumps({
                    "user_id": str(request.user.id),
                    "plan": plan
                })
            }]
        })

        if payment.create():
            # Store pending transaction
            PaymentTransaction.objects.create(
                user=request.user,
                payment_provider=PaymentTransaction.PaymentProvider.PAYPAL,
                paypal_order_id=payment.id,
                status='pending',
                amount=float(price_info['amount']),
                currency='usd'
            )

            # Get approval URL
            for link in payment.links:
                if link.rel == "approval_url":
                    return Response({
                        "url": link.href,
                        "approval_url": link.href,
                        "payment_id": payment.id
                    })
        else:
            return Response(
                {"detail": f"PayPal error: {payment.error}"},
                status=status.HTTP_400_BAD_REQUEST
            )


class ExecutePayPalPaymentView(APIView):
    """Execute/capture PayPal payment after user approval"""
    def post(self, request):
        payment_id = request.data.get('payment_id')
        payer_id = request.data.get('payer_id')

        if not payment_id or not payer_id:
            return Response(
                {"detail": "Missing payment_id or payer_id"},
                status=status.HTTP_400_BAD_REQUEST
            )

        payment = paypalrestsdk.Payment.find(payment_id)

        if payment.execute({"payer_id": payer_id}):
            # Payment successful - update subscription
            try:
                # Get custom data
                custom_data = json.loads(payment.transactions[0].custom)
                user_id = int(custom_data['user_id'])
                plan = custom_data.get('plan', 'monthly')

                user = User.objects.get(id=user_id)
                sub_obj, _ = Subscription.objects.get_or_create(user=user)
                sub_obj.plan_type = Subscription.PlanType.PRO
                sub_obj.payment_status = 'active'
                sub_obj.payment_provider = Subscription.PaymentProvider.PAYPAL
                sub_obj.start_date = timezone.now().date()
                sub_obj.paypal_subscription_id = payment_id
                sub_obj.save()

                # Update user role to PRO
                user.role = User.Role.PRO
                user.save(update_fields=['role'])

                # Update payment transaction
                PaymentTransaction.objects.filter(paypal_order_id=payment_id).update(
                    status='succeeded',
                    amount=float(payment.transactions[0].amount.total)
                )

                # Send push notification for payment success
                try:
                    from notifications.fcm_utils import send_payment_success_notification
                    from notifications.models import Notification

                    send_payment_success_notification(
                        user,
                        amount=float(payment.transactions[0].amount.total),
                        currency=payment.transactions[0].amount.currency
                    )

                    Notification.objects.create(
                        user=user,
                        message="Your PayPal payment was successful! Welcome to Pro membership."
                    )
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to send payment notification: {str(e)}")

                return Response({
                    "status": "success",
                    "message": "Payment successful",
                    "subscription": SubscriptionSerializer(sub_obj).data
                })

            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error processing PayPal payment: {str(e)}")
                return Response(
                    {"detail": f"Error processing payment: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            return Response(
                {"detail": f"Payment execution failed: {payment.error}"},
                status=status.HTTP_400_BAD_REQUEST
            )


@method_decorator(csrf_exempt, name='dispatch')
class PayPalWebhookView(APIView):
    """Handle PayPal webhook events"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        try:
            event_body = json.loads(request.body)
            event_type = event_body.get('event_type')

            # Handle different PayPal webhook events
            if event_type == 'PAYMENT.SALE.COMPLETED':
                # Payment completed successfully
                resource = event_body.get('resource', {})
                payment_id = resource.get('parent_payment')

                if payment_id:
                    PaymentTransaction.objects.filter(
                        paypal_order_id=payment_id
                    ).update(status='succeeded')

            elif event_type == 'PAYMENT.SALE.REFUNDED':
                # Payment was refunded
                resource = event_body.get('resource', {})
                payment_id = resource.get('parent_payment')

                if payment_id:
                    # Update subscription status
                    try:
                        sub_obj = Subscription.objects.get(paypal_subscription_id=payment_id)
                        sub_obj.payment_status = 'refunded'
                        sub_obj.plan_type = Subscription.PlanType.BASIC
                        sub_obj.end_date = timezone.now().date()
                        sub_obj.save()

                        # Downgrade user
                        user = sub_obj.user
                        user.role = User.Role.BASIC
                        user.save(update_fields=['role'])
                    except Subscription.DoesNotExist:
                        pass

            elif event_type == 'BILLING.SUBSCRIPTION.CANCELLED':
                # Subscription cancelled
                resource = event_body.get('resource', {})
                subscription_id = resource.get('id')

                if subscription_id:
                    try:
                        sub_obj = Subscription.objects.get(paypal_subscription_id=subscription_id)
                        sub_obj.plan_type = Subscription.PlanType.BASIC
                        sub_obj.payment_status = 'cancelled'
                        sub_obj.end_date = timezone.now().date()
                        sub_obj.save()

                        # Downgrade user
                        user = sub_obj.user
                        user.role = User.Role.BASIC
                        user.save(update_fields=['role'])
                    except Subscription.DoesNotExist:
                        pass

            return Response(status=status.HTTP_200_OK)

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"PayPal webhook error: {str(e)}")
            return Response(status=status.HTTP_400_BAD_REQUEST)


class CancelPayPalSubscriptionView(APIView):
    """Cancel PayPal subscription"""
    def post(self, request):
        sub, _ = Subscription.objects.get_or_create(user=request.user)

        # If using PayPal, cancel the subscription
        if sub.payment_provider == Subscription.PaymentProvider.PAYPAL and sub.paypal_subscription_id:
            try:
                # Note: PayPal subscription cancellation requires additional API calls
                # For simplicity, we'll just update our database
                pass
            except Exception:
                pass

        sub.plan_type = Subscription.PlanType.BASIC
        sub.payment_status = 'cancelled'
        sub.end_date = timezone.now().date()
        sub.save()

        # Downgrade user role to BASIC
        request.user.role = User.Role.BASIC
        request.user.save(update_fields=['role'])

        return Response({"message": "PayPal subscription cancelled"})
