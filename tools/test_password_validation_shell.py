from django.contrib.auth.models import User
from hello.models import Faculty
from django.test import Client

# Create test user (if not exists)
username = 'test_pw_user'
email = 'test_pw_user@example.com'
password = 'Current1!'

user, created = User.objects.get_or_create(username=username, defaults={'email': email})
if created:
    user.set_password(password)
    user.save()

# Ensure Faculty exists
faculty, fcreated = Faculty.objects.get_or_create(user=user, defaults={'first_name':'TPU','last_name':'User','email':email})
if fcreated:
    faculty.save()

c = Client()
logged = c.login(username=username, password=password)
print('Logged in:', logged)

# Attempt to change to an invalid password
resp = c.post('/staff/account/save/', {
    'firstName': faculty.first_name,
    'lastName': faculty.last_name,
    'email': faculty.email,
    'currentPassword': password,
    'newPassword': '@ste'
})
print('Status code:', resp.status_code)
print('Response content:', resp.content.decode())

# Clean up: reset password to original to avoid persistent test effect
user.set_password(password)
user.save()
print('Done')
