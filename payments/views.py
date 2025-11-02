from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import stripe
from .models import Subscription, PaymentTransaction
from .serializers import SubscriptionSerializer, PaymentTransactionSerializer

stripe.api_key = settings.STRIPE_SECRET_KEY
User = get_user_model()


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
            user=request.user, stripe_session_id=session.id, status='pending', amount=0, currency='usd'
        )
        return Response({"checkout_url": session.url})


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
