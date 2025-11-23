#!/usr/bin/env python
"""Test disabled account login behavior"""
import os
import django
import requests

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_mangement_api.settings')
django.setup()

from accounts.models import User

print("=" * 60)
print("Testing Disabled Account Login Flow")
print("=" * 60)

# Create test user
test_email = 'testdisabled@example.com'
test_username = 'testdisabled'
test_password = 'TestPass123!'

# Clean up if exists
User.objects.filter(email=test_email).delete()

# Create user
user = User.objects.create_user(
    username=test_username,
    email=test_email,
    password=test_password,
    is_verified=True,  # Make sure it's verified
    is_disabled=False  # Start as enabled
)

print(f"\n1. Created test user: {user.username}")
print(f"   Email: {user.email}")
print(f"   Verified: {user.is_verified}")
print(f"   Disabled: {user.is_disabled}")

# Test login when enabled
print("\n2. Testing login when account is ENABLED...")
try:
    response = requests.post(
        'http://127.0.0.1:8000/api/v1/auth/login/',
        json={'email': test_email, 'password': test_password}
    )
    if response.status_code == 200:
        print("   [OK] Login successful!")
        print(f"   Token received: {response.json()['access'][:20]}...")
    else:
        print(f"   [FAIL] Login failed: {response.json()}")
except Exception as e:
    print(f"   [ERROR] Error: {e}")

# Disable the account
user.is_disabled = True
user.is_active = False
user.save()

print(f"\n3. Disabled account:")
print(f"   is_disabled: {user.is_disabled}")
print(f"   is_active: {user.is_active}")

# Test login when disabled
print("\n4. Testing login when account is DISABLED...")
try:
    response = requests.post(
        'http://127.0.0.1:8000/api/v1/auth/login/',
        json={'email': test_email, 'password': test_password}
    )
    if response.status_code == 200:
        print("   [FAIL] Login succeeded (SHOULD HAVE FAILED!)")
    else:
        print(f"   [OK] Login blocked as expected!")
        print(f"   Status code: {response.status_code}")
        error_data = response.json()
        print(f"   Error details: {error_data}")

        # Check if proper error structure
        if 'account_disabled' in str(error_data):
            print("   [OK] Correct error flag 'account_disabled' present")
        if 'administrator' in str(error_data).lower():
            print("   [OK] Message mentions administrator")
        if 'contact support' in str(error_data).lower() or 'contact' in str(error_data).lower():
            print("   [OK] Message mentions contacting support")
except Exception as e:
    print(f"   Error: {e}")

# Enable the account back
user.is_disabled = False
user.is_active = True
user.save()

print(f"\n5. Re-enabled account:")
print(f"   is_disabled: {user.is_disabled}")
print(f"   is_active: {user.is_active}")

# Test login after re-enabling
print("\n6. Testing login after RE-ENABLING...")
try:
    response = requests.post(
        'http://127.0.0.1:8000/api/v1/auth/login/',
        json={'email': test_email, 'password': test_password}
    )
    if response.status_code == 200:
        print("   [OK] Login successful after re-enabling!")
    else:
        print(f"   [FAIL] Login failed: {response.json()}")
except Exception as e:
    print(f"   [ERROR] Error: {e}")

# Cleanup
user.delete()
print(f"\n7. Cleaned up test user")

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)
