"""
Diagnostic script to check user login status
Run with: python manage.py shell < check_user_status.py
"""
from accounts.models import User

print("\n" + "="*60)
print("USER LOGIN DIAGNOSTIC TOOL")
print("="*60)

# Prompt for email
email = input("\nEnter your email: ").strip()

try:
    user = User.objects.get(email=email)

    print(f"\n✓ User found: {user.username}")
    print("\n" + "-"*60)
    print("USER STATUS:")
    print("-"*60)
    print(f"Email:          {user.email}")
    print(f"Username:       {user.username}")
    print(f"Is Active:      {user.is_active} {'✓' if user.is_active else '✗ BLOCKED'}")
    print(f"Is Verified:    {user.is_verified} {'✓' if user.is_verified else '✗ BLOCKED'}")
    print(f"Is Disabled:    {user.is_disabled} {'✗ BLOCKED' if user.is_disabled else '✓'}")
    print(f"Is Staff:       {user.is_staff}")
    print(f"Is Superuser:   {user.is_superuser}")
    print(f"Role:           {user.get_role_display()}")
    print("-"*60)

    # Check what's blocking login
    blocking_reasons = []

    if not user.is_active:
        blocking_reasons.append("❌ Account is NOT ACTIVE (is_active=False)")

    if not user.is_verified:
        blocking_reasons.append("❌ Email is NOT VERIFIED (is_verified=False)")

    if user.is_disabled:
        blocking_reasons.append("❌ Account is DISABLED (is_disabled=True)")

    if blocking_reasons:
        print("\n🚫 LOGIN BLOCKED - REASONS:")
        print("-"*60)
        for reason in blocking_reasons:
            print(f"  {reason}")
        print("\n💡 FIX:")
        print("-"*60)

        if not user.is_verified:
            print("  To verify email, run:")
            print(f"  User.objects.filter(email='{email}').update(is_verified=True)")

        if not user.is_active:
            print("  To activate account, run:")
            print(f"  User.objects.filter(email='{email}').update(is_active=True)")

        if user.is_disabled:
            print("  To enable account, run:")
            print(f"  User.objects.filter(email='{email}').update(is_disabled=False)")
    else:
        print("\n✅ ALL CHECKS PASSED - User should be able to login!")
        print("\nIf you still can't login, check:")
        print("  1. Password is correct")
        print("  2. Check server logs for error details")
        print("  3. Verify JWT settings are correct")

    print("-"*60)

except User.DoesNotExist:
    print(f"\n❌ ERROR: No user found with email '{email}'")
    print("\nAvailable users:")
    for u in User.objects.all()[:10]:
        print(f"  - {u.email} ({u.username})")

print("\n" + "="*60 + "\n")
