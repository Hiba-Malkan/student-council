from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from .models import Feedback


class FeedbackApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('sam', 'sam@example.com', 'password123')
        self.staff = User.objects.create_user('staff', 'staff@example.com', 'password123', is_staff=True)

    def test_anyone_can_submit_feedback_and_authenticated_submitter_is_recorded(self):
        response = self.client.post('/api/feedback/', {
            'name': 'Anonymous', 'email': 'anon@example.com', 'type': 'BUG', 'priority': 'HIGH',
            'subject': 'Broken button', 'description': 'The submit button does nothing.',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        anonymous = Feedback.objects.get()
        self.assertIsNone(anonymous.submitted_by)

        self.client.force_authenticate(self.user)
        response = self.client.post('/api/feedback/', {
            'subject': 'Idea', 'description': 'Add a dark mode setting.',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Feedback.objects.get(subject='Idea').submitted_by, self.user)

    def test_only_staff_can_list_and_manage_feedback(self):
        feedback = Feedback.objects.create(submitted_by=self.user, subject='Bug', description='A reproducible issue')
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get('/api/feedback/').status_code, 403)
        self.assertEqual(self.client.post(f'/api/feedback/{feedback.id}/update_status/', {'status': 'RESOLVED'}, format='json').status_code, 403)

        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.get('/api/feedback/').status_code, 200)
        response = self.client.post(f'/api/feedback/{feedback.id}/update_status/', {'status': 'RESOLVED'}, format='json')
        self.assertEqual(response.status_code, 200)
        feedback.refresh_from_db()
        self.assertEqual(feedback.status, 'RESOLVED')
        self.assertIsNotNone(feedback.resolved_at)
        self.assertEqual(self.client.post(f'/api/feedback/{feedback.id}/update_priority/', {'priority': 'CRITICAL'}, format='json').data['priority'], 'CRITICAL')
        self.assertEqual(self.client.post(f'/api/feedback/{feedback.id}/add_notes/', {'notes': 'Looking into it'}, format='json').status_code, 200)
        feedback.refresh_from_db()
        self.assertIn('Looking into it', feedback.admin_notes)

    def test_management_actions_validate_missing_or_invalid_data(self):
        feedback = Feedback.objects.create(subject='Bug', description='A reproducible issue')
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.post(f'/api/feedback/{feedback.id}/update_status/', {'status': 'BAD'}, format='json').status_code, 400)
        self.assertEqual(self.client.post(f'/api/feedback/{feedback.id}/update_priority/', {'priority': 'BAD'}, format='json').status_code, 400)
        self.assertEqual(self.client.post(f'/api/feedback/{feedback.id}/add_notes/', {'notes': ' '}, format='json').status_code, 400)
