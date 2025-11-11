from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Faculty


class HelloTests(TestCase):
	def test_home_redirects_when_not_logged_in(self):
		response = self.client.get(reverse('staff_dashboard'))
		# staff_dashboard requires login; should redirect to login
		self.assertEqual(response.status_code, 302)

	def test_save_account_settings_rejects_short_password(self):
		# Create test user and faculty
		username = 'pwtestuser'
		password = 'Current1!'
		user = User.objects.create_user(username=username, password=password, email='pwtest@example.com')
		faculty = Faculty.objects.create(user=user, first_name='Pw', last_name='Test', email='pwtest@example.com')

		c = Client()
		logged = c.login(username=username, password=password)
		self.assertTrue(logged)

		resp = c.post('/staff/account/save/', {
			'firstName': faculty.first_name,
			'lastName': faculty.last_name,
			'email': faculty.email,
			'currentPassword': password,
			'newPassword': '@ste'
		})

		# Should be rejected with 400 and an error message about length
		self.assertEqual(resp.status_code, 400)
		data = resp.json()
		self.assertFalse(data.get('success', True))
		errors = data.get('errors', [])
		self.assertTrue(any('at least 8' in e or 'New password must have' in e for e in errors))

