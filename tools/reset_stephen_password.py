from django.contrib.auth.models import User
from hello.models import Faculty

print("=" * 70)
print("STEPHEN NASH PASSWORD RESET TOOL")
print("=" * 70)

# Try to find Stephen Nash by name, username, or email
print("\n[1] Searching for Stephen Nash...")

# Search by name
qs = User.objects.filter(first_name__iexact='Stephen', last_name__iexact='Nash')
if qs.exists():
    u = qs.first()
    print(f"✓ Found by name: {u.first_name} {u.last_name}")
else:
    # Try username or email containing 'stephen'
    u = User.objects.filter(username__icontains='stephen').first()
    if u:
        print(f"✓ Found by username: {u.username}")
    else:
        u = User.objects.filter(email__icontains='stephen').first()
        if u:
            print(f"✓ Found by email: {u.email}")

if not u:
    print("✗ No user found for Stephen Nash. Showing all users:")
    all_users = User.objects.all()
    for user in all_users:
        print(f"  - {user.first_name} {user.last_name} ({user.username}, {user.email})")
    print("\nPlease copy the username or email and I can reset that user's password.")
else:
    print(f"\n[2] Account details for {u.first_name} {u.last_name}:")
    print(f"  - Username: {u.username}")
    print(f"  - Email: {u.email}")
    print(f"  - Is Active: {u.is_active}")
    print(f"  - Last Login: {u.last_login}")
    
    try:
        f = Faculty.objects.get(user=u)
        print(f"  - Faculty Profile: Yes")
        print(f"  - Faculty Email: {f.email}")
    except Faculty.DoesNotExist:
        print(f"  - Faculty Profile: No")
    
    if not u.is_active:
        print("\n⚠️  WARNING: This account is INACTIVE. Activating it...")
        u.is_active = True
        u.save()
        print("✓ Account activated.")
    
    print(f"\n[3] Setting temporary password...")
    temp_password = "TempPass123!"
    u.set_password(temp_password)
    u.save()
    print(f"✓ Password reset successfully!")
    print(f"\n" + "=" * 70)
    print(f"TEMPORARY PASSWORD: {temp_password}")
    print("=" * 70)
    print(f"\nUsername: {u.username}")
    print(f"Temporary Password: {temp_password}")
    print(f"\n⚠️  IMPORTANT SECURITY NOTES:")
    print(f"  1. Share this password SECURELY with the user (NOT via email/chat)")
    print(f"  2. User MUST change password immediately after first login")
    print(f"  3. This is a one-time use temporary credential")
    print("=" * 70)
