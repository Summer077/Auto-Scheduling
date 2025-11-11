from django.contrib.auth.models import User
from hello.models import Faculty
from django.test import Client

username = 'test_pw_user'
email = 'test_pw_user@example.com'
password = 'Current1!'

user, created = User.objects.get_or_create(username=username, defaults={'email': email})
if created:
    user.set_password(password)
    user.save()

faculty, fcreated = Faculty.objects.get_or_create(user=user, defaults={'first_name':'TPU','last_name':'User','email':email})
if fcreated:
    faculty.save()

c = Client()
logged = c.login(username=username, password=password)
print('LOGGED_IN:', logged)

resp = c.post('/staff/account/save/', {
    'firstName': faculty.first_name,
    'lastName': faculty.last_name,
    'email': faculty.email,
    'currentPassword': password,
    'newPassword': '@ste'
})
print('RESP_STATUS:', resp.status_code)
print('RESP_CONTENT:\n---START---')
print(resp.content.decode(errors='replace'))
print('---END---')

user.set_password(password)
user.save()
print('CLEANUP_DONE')
