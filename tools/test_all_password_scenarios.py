from django.contrib.auth.models import User
from hello.models import Faculty
from django.test import Client

print("Testing password validation scenarios...")

# Create test user
username = 'testpw'
email = 'testpw@example.com'
current_pw = 'Current1!'

user, _ = User.objects.get_or_create(username=username, defaults={'email': email})
user.set_password(current_pw)
user.save()

faculty, _ = Faculty.objects.get_or_create(user=user, defaults={'first_name':'Test','last_name':'User','email':email})

c = Client()
c.login(username=username, password=current_pw)

print("\n1. TEST: Wrong current password, no new password")
resp = c.post('/staff/account/save/', {
    'firstName': 'Test',
    'lastName': 'User',
    'email': email,
    'currentPassword': 'WrongPassword123!',
    'newPassword': ''
})
print(f"   Status: {resp.status_code}, Success: {resp.json().get('success')}")
if resp.status_code >= 400:
    print(f"   Errors: {resp.json().get('errors')}")

print("\n2. TEST: Wrong current password WITH new password")
resp = c.post('/staff/account/save/', {
    'firstName': 'Test',
    'lastName': 'User',
    'email': email,
    'currentPassword': 'WrongPassword123!',
    'newPassword': 'NewPass1!'
})
print(f"   Status: {resp.status_code}, Success: {resp.json().get('success')}")
if resp.status_code >= 400:
    print(f"   Errors: {resp.json().get('errors')}")

print("\n3. TEST: Correct current password, short new password (@steph)")
resp = c.post('/staff/account/save/', {
    'firstName': 'Test',
    'lastName': 'User',
    'email': email,
    'currentPassword': current_pw,
    'newPassword': '@steph'
})
print(f"   Status: {resp.status_code}, Success: {resp.json().get('success')}")
if resp.status_code >= 400:
    print(f"   Errors: {resp.json().get('errors')}")

print("\n4. TEST: Correct current password, valid new password (NewPass1!)")
resp = c.post('/staff/account/save/', {
    'firstName': 'Test',
    'lastName': 'User',
    'email': email,
    'currentPassword': current_pw,
    'newPassword': 'NewPass1!'
})
print(f"   Status: {resp.status_code}, Success: {resp.json().get('success')}")
if resp.status_code >= 400:
    print(f"   Errors: {resp.json().get('errors')}")
else:
    print(f"   Message: {resp.json().get('message')}")

print("\nAll tests complete!")
