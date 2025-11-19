#!/usr/bin/env python
"""
Quick test script to verify email sending functionality
Run this with: python test_email.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_mangement_api.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.utils import send_password_reset_email
from django.conf import settings

User = get_user_model()

def test_forgot_password_email():
    """Test sending password reset email"""

    print("=" * 60)
    print("TESTING PASSWORD RESET EMAIL")
    print("=" * 60)

    # Email configuration
    print("\n[*] Email Configuration:")
    print(f"   Backend: {settings.EMAIL_BACKEND}")
    print(f"   Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
    print(f"   User: {settings.EMAIL_HOST_USER}")
    print(f"   From: {settings.DEFAULT_FROM_EMAIL}")
    print(f"   Frontend URL: {settings.FRONTEND_URL}")

    # Get test user
    test_email = "bunsong601@gmail.com"
    print(f"\n[*] Looking for user with email: {test_email}")

    try:
        user = User.objects.get(email=test_email)
        print(f"   [OK] User found: {user.username} (ID: {user.id})")
    except User.DoesNotExist:
        print(f"   [ERROR] No user found with email: {test_email}")
        print("\n[INFO] Create a user first:")
        print(f"   python manage.py createsuperuser")
        return

    # Send password reset email
    print(f"\n[*] Sending password reset email to: {test_email}")
    print("   Please wait...")

    try:
        success = send_password_reset_email(user)

        if success:
            print("\n[SUCCESS] Password reset email sent!")
            print(f"\n[*] Check your inbox at: {test_email}")
            print("\n[*] What to check:")
            print("   1. Check your Gmail inbox")
            print("   2. Look for email from:", settings.DEFAULT_FROM_EMAIL)
            print("   3. Subject: 'Password Reset Request - Task Management System'")
            print("   4. If not in inbox, check spam/junk folder")
            print("\n[*] The email contains:")
            print(f"   - Beautiful HTML template with blue gradient")
            print(f"   - Reset button linking to: {settings.FRONTEND_URL}/reset-password/...")
            print(f"   - Security information")
            print(f"   - Token expires in 1 hour")
        else:
            print("\n[ERROR] FAILED to send email!")
            print("   Check the error messages above")

    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        print("\n[*] Troubleshooting:")
        print("   1. Check if EMAIL_HOST_PASSWORD is correct in .env")
        print("   2. Verify Gmail account has 'App Password' enabled")
        print("   3. Check internet connection")
        print("   4. Review Django logs: tail -f logs/django.log")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_forgot_password_email()
