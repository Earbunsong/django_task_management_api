#!/usr/bin/env python
"""
Quick script to manually verify a user
Run with: python manage.py shell < verify_user_quick.py
"""

from accounts.models import User

# ===== CONFIGURE THIS =====
USER_EMAIL = "bunsong601@gmail.com"  # Change to your email
# ==========================

print("=" * 60)
print("MANUAL USER VERIFICATION SCRIPT")
print("=" * 60)

try:
    # Find the user
    user = User.objects.get(email=USER_EMAIL)

    print(f"\n✅ Found user:")
    print(f"   Username: {user.username}")
    print(f"   Email: {user.email}")
    print(f"   User ID: {user.id}")
    print(f"   Is Active: {user.is_active}")
    print(f"   Is Disabled: {user.is_disabled}")
    print(f"   Role: {user.role}")

    print(f"\n📧 Verification Status:")
    print(f"   BEFORE: is_verified = {user.is_verified}")

    # Verify the user
    user.is_verified = True
    user.save(update_fields=['is_verified'])

    # Reload from database to confirm
    user.refresh_from_db()

    print(f"   AFTER:  is_verified = {user.is_verified}")

    if user.is_verified:
        print(f"\n🎉 SUCCESS! User {user.username} is now verified!")
        print(f"\n✅ You can now login with:")
        print(f"   Email: {user.email}")
        print(f"   Password: (your password)")
    else:
        print(f"\n❌ ERROR: Failed to verify user!")

except User.DoesNotExist:
    print(f"\n❌ ERROR: No user found with email '{USER_EMAIL}'")
    print(f"\n📋 Available users:")

    all_users = User.objects.all()
    if all_users.exists():
        for u in all_users:
            status = "✅ Verified" if u.is_verified else "❌ Not Verified"
            print(f"   - {u.email} ({u.username}) - {status}")
    else:
        print("   (No users in database)")

    print(f"\n💡 TIP: Update USER_EMAIL in this script to one of the emails above")

except Exception as e:
    print(f"\n❌ UNEXPECTED ERROR: {e}")

print("\n" + "=" * 60)
