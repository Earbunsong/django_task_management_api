#!/usr/bin/env python
"""Test email verification flow"""
import os
import django
import requests
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_mangement_api.settings')
django.setup()

from accounts.models import User
from accounts.utils import email_verification_token

# Create a test user
test_email = 'testverify@example.com'
print(f"Testing verification flow with {test_email}...")

# Delete if exists
User.objects.filter(email=test_email).delete()

# Create new unverified user
user = User.objects.create_user(
    username='testverify',
    email=test_email,
    password='testpassword123',
    is_verified=False
)
print(f"[OK] Created user: {user.username}, is_verified={user.is_verified}")

# Generate verification token
uid = urlsafe_base64_encode(force_bytes(user.pk))
token = email_verification_token.make_token(user)
verify_url = f'http://127.0.0.1:8000/api/v1/auth/verify/{uid}/{token}/'

print(f"[OK] Generated verification URL: {verify_url}")

# Call verification endpoint
response = requests.get(verify_url)
print(f"[OK] API Response: {response.status_code} - {response.json()}")

# Check if user is now verified
user.refresh_from_db()
print(f"[OK] User after verification: is_verified={user.is_verified}")

if user.is_verified:
    print("\n[SUCCESS] Verification flow is working!")
else:
    print("\n[FAILED] User is still not verified!")

# Cleanup
user.delete()
print(f"[OK] Cleaned up test user")
