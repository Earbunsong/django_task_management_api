"""
Test script for Stripe payment endpoints
Run with: python test_stripe_payments.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_mangement_api.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from rest_framework_simplejwt.tokens import RefreshToken
from payments.models import Subscription, PaymentTransaction

User = get_user_model()

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_success(message):
    print(f"[OK] {message}")

def print_error(message):
    print(f"[ERROR] {message}")

def print_info(message):
    print(f"[INFO] {message}")

def create_test_user():
    """Create or get test user"""
    print_section("Setting Up Test User")

    try:
        user = User.objects.filter(email='testuser@example.com').first()
        if not user:
            user = User.objects.create_user(
                username='testuser',
                email='testuser@example.com',
                password='testpass123',
                role=User.Role.BASIC
            )
            print_success("Created new test user: testuser@example.com")
        else:
            print_info("Using existing test user: testuser@example.com")

        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        print_info(f"User ID: {user.id}")
        print_info(f"User Role: {user.role}")
        print_info(f"JWT Token: {access_token[:30]}...")

        return user, access_token
    except Exception as e:
        print_error(f"Failed to create test user: {str(e)}")
        return None, None

def test_get_subscription(client, token):
    """Test GET /api/v1/payment/subscription/"""
    print_section("Test 1: Get User Subscription")

    try:
        response = client.get(
            '/api/v1/payment/subscription/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )

        print_info(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print_success("Successfully retrieved subscription")
            print_info(f"Plan Type: {data.get('plan_type', 'N/A')}")
            print_info(f"Payment Status: {data.get('payment_status', 'N/A')}")
            print_info(f"Payment Provider: {data.get('payment_provider', 'N/A')}")
            print_info(f"Start Date: {data.get('start_date', 'N/A')}")
            return True
        else:
            print_error(f"Failed with status {response.status_code}")
            print_error(f"Response: {response.content.decode()[:200]}")
            return False
    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False

def test_payment_history(client, token):
    """Test GET /api/v1/payment/history/"""
    print_section("Test 2: Get Payment History")

    try:
        response = client.get(
            '/api/v1/payment/history/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )

        print_info(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print_success("Successfully retrieved payment history")
            print_info(f"Total Payments: {len(data)}")

            if len(data) > 0:
                for idx, payment in enumerate(data[:3], 1):
                    print_info(f"  Payment {idx}:")
                    print_info(f"    - Amount: ${payment.get('amount', 0)} {payment.get('currency', 'USD').upper()}")
                    print_info(f"    - Status: {payment.get('status', 'N/A')}")
                    print_info(f"    - Provider: {payment.get('payment_provider', 'N/A')}")
                    print_info(f"    - Date: {payment.get('created_at', 'N/A')[:10]}")
            else:
                print_info("  No payment history found")
            return True
        else:
            print_error(f"Failed with status {response.status_code}")
            print_error(f"Response: {response.content.decode()[:200]}")
            return False
    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        return False

def test_create_stripe_session(client, token):
    """Test POST /api/v1/payment/create-session/"""
    print_section("Test 3: Create Stripe Checkout Session")

    try:
        response = client.post(
            '/api/v1/payment/create-session/',
            data={'plan': 'monthly'},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )

        print_info(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print_success("Successfully created Stripe checkout session")

            if 'url' in data:
                print_info(f"Checkout URL: {data['url'][:60]}...")

                # Check if payment transaction was created
                from payments.models import PaymentTransaction
                latest_payment = PaymentTransaction.objects.filter(
                    user__email='testuser@example.com'
                ).order_by('-created_at').first()

                if latest_payment:
                    print_success("Payment transaction created in database")
                    print_info(f"  - Transaction ID: {latest_payment.id}")
                    print_info(f"  - Provider: {latest_payment.payment_provider}")
                    print_info(f"  - Status: {latest_payment.status}")
                    print_info(f"  - Stripe Session ID: {latest_payment.stripe_session_id[:30]}...")

                return True
            else:
                print_error("No checkout URL in response")
                return False
        elif response.status_code == 500:
            print_error("Internal Server Error (500)")
            print_error(f"Response: {response.content.decode()[:500]}")
            return False
        else:
            print_error(f"Failed with status {response.status_code}")
            print_error(f"Response: {response.content.decode()[:200]}")
            return False
    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_check_payment_status(client, token):
    """Test POST /api/v1/payment/check-status/"""
    print_section("Test 4: Check Payment Status")

    try:
        response = client.post(
            '/api/v1/payment/check-status/',
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )

        print_info(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print_success("Successfully checked payment status")
            print_info(f"Status: {data.get('status', 'N/A')}")
            print_info(f"Message: {data.get('message', 'N/A')}")
            print_info(f"Is Pro: {data.get('is_pro', False)}")
            print_info(f"Plan Type: {data.get('plan_type', 'N/A')}")
            return True
        elif response.status_code == 500:
            print_error("Internal Server Error (500)")
            print_error(f"Response: {response.content.decode()[:500]}")
            return False
        else:
            print_error(f"Failed with status {response.status_code}")
            print_error(f"Response: {response.content.decode()[:200]}")
            return False
    except Exception as e:
        print_error(f"Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_stripe_configuration():
    """Check if Stripe is configured"""
    print_section("Checking Stripe Configuration")

    from django.conf import settings

    has_secret_key = bool(settings.STRIPE_SECRET_KEY)
    has_webhook_secret = bool(settings.STRIPE_WEBHOOK_SECRET)
    has_monthly_price = bool(settings.STRIPE_PRICE_ID_MONTHLY)
    has_annual_price = bool(settings.STRIPE_PRICE_ID_ANNUAL)

    if has_secret_key:
        print_success("STRIPE_SECRET_KEY is configured")
    else:
        print_error("STRIPE_SECRET_KEY is NOT configured")

    if has_webhook_secret:
        print_success("STRIPE_WEBHOOK_SECRET is configured")
    else:
        print_error("STRIPE_WEBHOOK_SECRET is NOT configured (optional for testing)")

    if has_monthly_price:
        print_success("STRIPE_PRICE_ID_MONTHLY is configured")
    else:
        print_error("STRIPE_PRICE_ID_MONTHLY is NOT configured")

    if has_annual_price:
        print_success("STRIPE_PRICE_ID_ANNUAL is configured")
    else:
        print_error("STRIPE_PRICE_ID_ANNUAL is NOT configured")

    return has_secret_key and has_monthly_price

def check_database_models():
    """Check if database models have correct fields"""
    print_section("Checking Database Models")

    try:
        from payments.models import Subscription, PaymentTransaction

        # Check Subscription fields
        subscription_fields = [f.name for f in Subscription._meta.get_fields()]
        required_fields = ['payment_provider', 'paypal_subscription_id', 'stripe_subscription_id']

        print_info("Subscription Model Fields:")
        for field in required_fields:
            if field in subscription_fields:
                print_success(f"  + {field}")
            else:
                print_error(f"  - {field} MISSING")

        # Check PaymentTransaction fields
        payment_fields = [f.name for f in PaymentTransaction._meta.get_fields()]
        required_payment_fields = ['payment_provider', 'paypal_order_id', 'stripe_session_id']

        print_info("\nPaymentTransaction Model Fields:")
        for field in required_payment_fields:
            if field in payment_fields:
                print_success(f"  + {field}")
            else:
                print_error(f"  - {field} MISSING")

        all_present = all(f in subscription_fields for f in required_fields) and \
                      all(f in payment_fields for f in required_payment_fields)

        return all_present
    except Exception as e:
        print_error(f"Error checking models: {str(e)}")
        return False

def main():
    """Main test runner"""
    print("\n")
    print("=" * 60)
    print(" " * 15 + "STRIPE PAYMENT TEST SUITE")
    print("=" * 60)

    # Pre-flight checks
    stripe_configured = check_stripe_configuration()
    models_correct = check_database_models()

    if not models_correct:
        print("\n" + "!"*60)
        print("CRITICAL: Database models are missing required fields!")
        print("Please run: python manage.py migrate payments")
        print("!"*60)
        return

    if not stripe_configured:
        print("\n" + "!"*60)
        print("WARNING: Stripe is not fully configured!")
        print("Some tests may fail. Please check your .env file.")
        print("!"*60)

    # Create test user and get token
    user, token = create_test_user()
    if not user or not token:
        print_error("Failed to create test user. Exiting.")
        return

    # Create Django test client with proper server name
    client = Client(SERVER_NAME='localhost')

    # Run tests
    results = {
        'Get Subscription': test_get_subscription(client, token),
        'Payment History': test_payment_history(client, token),
        'Create Stripe Session': test_create_stripe_session(client, token),
        'Check Payment Status': test_check_payment_status(client, token),
    }

    # Print summary
    print_section("TEST SUMMARY")

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")

    print("\n" + "-"*60)
    print(f"Total: {passed}/{total} tests passed")
    print("-"*60)

    if passed == total:
        print("\n*** All Stripe payment tests PASSED! ***\n")
    else:
        print(f"\n*** WARNING: {total - passed} test(s) FAILED. Check errors above. ***\n")

    # Cleanup option
    print_info("\nTest user 'testuser@example.com' was created/used for testing.")
    print_info("You can delete it manually from Django admin if needed.")

if __name__ == '__main__':
    main()
