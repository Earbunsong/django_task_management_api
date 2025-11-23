"""
Quick script to verify the user devkh31@gmail.com
Run with: python manage.py shell < verify_devkh.py
"""
from accounts.models import User

email = "devkh31@gmail.com"

try:
    user = User.objects.get(email=email)

    print(f"\n{'='*60}")
    print(f"BEFORE:")
    print(f"{'='*60}")
    print(f"Email:       {user.email}")
    print(f"Username:    {user.username}")
    print(f"is_verified: {user.is_verified}")
    print(f"is_active:   {user.is_active}")
    print(f"is_disabled: {user.is_disabled}")

    # Fix all potential blocking issues
    user.is_verified = True
    user.is_active = True
    user.is_disabled = False
    user.save()

    print(f"\n{'='*60}")
    print(f"AFTER:")
    print(f"{'='*60}")
    print(f"Email:       {user.email}")
    print(f"Username:    {user.username}")
    print(f"is_verified: {user.is_verified}")
    print(f"is_active:   {user.is_active}")
    print(f"is_disabled: {user.is_disabled}")
    print(f"\n✅ SUCCESS! User {user.username} can now login!")
    print(f"{'='*60}\n")

except User.DoesNotExist:
    print(f"\n❌ ERROR: User with email '{email}' not found!\n")
