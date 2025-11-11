from django.contrib.auth.models import User
from hello.models import Faculty

u = User.objects.get(username='stephennash.baldonado')
print(f"Account: {u.first_name} {u.last_name}")
print(f"Username: {u.username}")
print(f"Email: {u.email}")
print(f"Is Active: {u.is_active}")

if not u.is_active:
    u.is_active = True
    u.save()
    print("Status: ACTIVATED")

temp_password = "TempPass123!"
u.set_password(temp_password)
u.save()

print(f"\n{'='*60}")
print("PASSWORD RESET COMPLETE")
print(f"{'='*60}")
print(f"Username: {u.username}")
print(f"Temporary Password: {temp_password}")
print(f"\nShare this securely with Stephen.")
print(f"User must change it immediately after login.")
print(f"{'='*60}")
