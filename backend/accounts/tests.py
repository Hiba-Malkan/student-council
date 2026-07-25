from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from .models import ContactMessage, PasswordResetOTP, Role, User


class AccountModelTests(TestCase):
    def test_duty_roster_visibility_uses_user_override_then_role_default(self):
        visible_role = Role.objects.create(name='Captain', show_in_duty_roster=True)
        user = User.objects.create_user('sam', 'sam@example.com', 'password123', role=visible_role)

        self.assertTrue(user.is_visible_in_duty_roster)

        user.show_in_duty_roster = False
        self.assertFalse(user.is_visible_in_duty_roster)

        user.role = None
        user.show_in_duty_roster = None
        self.assertFalse(user.is_visible_in_duty_roster)

    def test_password_reset_otp_expires_and_can_be_marked_used(self):
        user = User.objects.create_user('sam', 'sam@example.com', 'password123')
        otp = PasswordResetOTP.create_otp(user, '127.0.0.1')

        self.assertEqual(len(otp.otp), 6)
        self.assertTrue(otp.otp.isdigit())
        self.assertTrue(otp.is_valid())

        otp.mark_as_used()
        self.assertFalse(otp.is_valid())

        expired = PasswordResetOTP.objects.create(
            user=user, otp='123456', expires_at=timezone.now() - timedelta(seconds=1)
        )
        self.assertFalse(expired.is_valid())


class AccountApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('sam', 'sam@example.com', 'password123')

    def test_login_returns_jwt_tokens_for_valid_credentials(self):
        response = self.client.post(
            '/api/accounts/login/', {'username': 'sam', 'password': 'password123'}, format='json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user']['username'], 'sam')
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])

    def test_login_rejects_invalid_credentials(self):
        response = self.client.post(
            '/api/accounts/login/', {'username': 'sam', 'password': 'wrong-password'}, format='json'
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data['error'], 'Invalid credentials')

    def test_reset_password_consumes_valid_otp(self):
        otp = PasswordResetOTP.objects.create(
            user=self.user, otp='123456', expires_at=timezone.now() + timedelta(minutes=10)
        )

        response = self.client.post('/api/accounts/reset-password/', {
            'identifier': self.user.email,
            'otp': otp.otp,
            'new_password': 'new-password123',
            'confirm_password': 'new-password123',
        }, format='json')

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        otp.refresh_from_db()
        self.assertTrue(self.user.check_password('new-password123'))
        self.assertTrue(otp.is_used)

    def test_contact_message_is_public_but_only_staff_can_view_and_reply(self):
        response = self.client.post('/api/accounts/contact-admin/', {
            'name': 'Guest', 'email': 'guest@example.com', 'subject': 'Need help',
            'message': 'Please help me access my account.',
        }, format='json', HTTP_X_FORWARDED_FOR='203.0.113.10')
        self.assertEqual(response.status_code, 201)
        message = ContactMessage.objects.get()
        self.assertEqual(message.ip_address, '203.0.113.10')

        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get('/api/accounts/contact-messages/').status_code, 200)
        self.assertEqual(self.client.get('/api/accounts/contact-messages/').data['results'], [])

        staff = User.objects.create_user('staff', 'staff@example.com', 'password123', is_staff=True)
        self.client.force_authenticate(staff)
        response = self.client.patch(f'/api/accounts/contact-messages/{message.id}/respond/', {
            'admin_response': 'We reset your access.', 'status': 'resolved',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        message.refresh_from_db()
        self.assertEqual(message.responded_by, staff)
        self.assertIsNotNone(message.responded_at)
