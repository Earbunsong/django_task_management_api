#!/usr/bin/env python
"""
PayPal Payment Testing Script

This script helps you test PayPal payment integration.
It will guide you through the complete payment flow.
"""

import requests
import json
from getpass import getpass

# Configuration
BASE_URL = "http://127.0.0.1:8000/api/v1"

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")

def print_success(text):
    """Print success message"""
    print(f"✅ {text}")

def print_error(text):
    """Print error message"""
    print(f"❌ {text}")

def print_info(text):
    """Print info message"""
    print(f"ℹ️  {text}")

def get_auth_token():
    """Get JWT token by logging in"""
    print_header("Step 1: Login to get JWT token")

    username = input("Enter your username: ")
    password = getpass("Enter your password: ")

    try:
        response = requests.post(
            f"{BASE_URL}/accounts/login/",
            json={"username": username, "password": password}
        )

        if response.status_code == 200:
            data = response.json()
            token = data.get('access')
            print_success("Login successful!")
            print_info(f"Token: {token[:20]}...")
            return token
        else:
            print_error(f"Login failed: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return None

def check_subscription(token):
    """Check current subscription status"""
    print_header("Step 2: Check Current Subscription")

    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(f"{BASE_URL}/payment/subscription/", headers=headers)

        if response.status_code == 200:
            data = response.json()
            print_success("Current subscription status:")
            print(f"  Plan: {data.get('plan_type', 'N/A')}")
            print(f"  Status: {data.get('payment_status', 'N/A')}")
            print(f"  Provider: {data.get('payment_provider', 'N/A')}")
            print(f"  Start: {data.get('start_date', 'N/A')}")
            return data
        else:
            print_error(f"Failed to get subscription: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return None

def create_paypal_order(token, plan="monthly"):
    """Create a PayPal payment order"""
    print_header("Step 3: Create PayPal Payment Order")

    print(f"Creating PayPal order for {plan} plan...")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/payment/paypal/create-order/",
            headers=headers,
            json={"plan": plan}
        )

        if response.status_code == 200:
            data = response.json()
            approval_url = data.get('approval_url') or data.get('url')
            payment_id = data.get('payment_id')

            print_success("PayPal order created successfully!")
            print(f"\n  Payment ID: {payment_id}")
            print(f"\n  Approval URL: {approval_url}")

            print("\n" + "─" * 60)
            print_info("NEXT STEPS:")
            print("  1. Copy the approval URL above")
            print("  2. Open it in your browser")
            print("  3. Login to PayPal Sandbox account")
            print("  4. Complete the payment")
            print("  5. You'll be redirected back")
            print("  6. Copy the PayerID and PaymentID from URL")
            print("─" * 60 + "\n")

            return {
                'payment_id': payment_id,
                'approval_url': approval_url
            }
        else:
            print_error(f"Failed to create order: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return None

def execute_paypal_payment(token):
    """Execute PayPal payment after user approval"""
    print_header("Step 4: Execute PayPal Payment")

    print("After completing payment on PayPal, you need to execute it.")
    print("The redirect URL will contain PayerID and token parameters.\n")

    payment_id = input("Enter Payment ID (from Step 3 or URL): ")
    payer_id = input("Enter Payer ID (from redirect URL): ")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/payment/paypal/execute-payment/",
            headers=headers,
            json={
                "payment_id": payment_id,
                "payer_id": payer_id
            }
        )

        if response.status_code == 200:
            data = response.json()
            print_success("Payment executed successfully!")
            print(f"\n  Status: {data.get('status')}")
            print(f"  Message: {data.get('message')}")

            if 'subscription' in data:
                sub = data['subscription']
                print(f"\n  Subscription updated:")
                print(f"    Plan: {sub.get('plan_type')}")
                print(f"    Status: {sub.get('payment_status')}")
                print(f"    Provider: {sub.get('payment_provider')}")

            return data
        else:
            print_error(f"Failed to execute payment: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return None

def check_payment_history(token):
    """Check payment history"""
    print_header("Step 5: Check Payment History")

    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(f"{BASE_URL}/payment/history/", headers=headers)

        if response.status_code == 200:
            payments = response.json()

            if payments:
                print_success(f"Found {len(payments)} payment(s):")
                for payment in payments:
                    print(f"\n  Payment #{payment['id']}:")
                    print(f"    Provider: {payment['payment_provider']}")
                    print(f"    Amount: ${payment['amount']} {payment['currency'].upper()}")
                    print(f"    Status: {payment['status']}")
                    print(f"    Date: {payment['created_at']}")
                    if payment['paypal_order_id']:
                        print(f"    PayPal Order ID: {payment['paypal_order_id']}")
            else:
                print_info("No payment history found.")

            return payments
        else:
            print_error(f"Failed to get payment history: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return None

def main():
    """Main testing flow"""
    print("\n" + "🧪" * 30)
    print(" " * 10 + "PayPal Payment Testing Tool")
    print("🧪" * 30)

    # Step 1: Login
    token = get_auth_token()
    if not token:
        print_error("Cannot proceed without authentication token.")
        return

    # Step 2: Check current subscription
    subscription = check_subscription(token)

    # Step 3: Choose plan and create order
    print("\nAvailable plans:")
    print("  1. Monthly ($9.99)")
    print("  2. Annual ($99.99)")

    plan_choice = input("\nSelect plan (1 or 2): ")
    plan = "monthly" if plan_choice == "1" else "annual"

    order = create_paypal_order(token, plan)

    if not order:
        print_error("Cannot proceed without PayPal order.")
        return

    print("\n" + "⏸️ " * 20)
    print("PAUSED: Complete the payment in your browser")
    print("⏸️ " * 20)

    input("\nPress ENTER when you've completed payment on PayPal...")

    # Step 4: Execute payment
    result = execute_paypal_payment(token)

    if result:
        # Step 5: Verify with payment history
        check_payment_history(token)

        # Final verification
        print_header("Final Verification")
        check_subscription(token)

        print("\n" + "✅" * 30)
        print(" " * 10 + "Testing Complete!")
        print("✅" * 30 + "\n")
    else:
        print_error("Payment execution failed. Please try again.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Testing cancelled by user.")
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
