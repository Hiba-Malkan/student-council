from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Role, User
from .models import GatePass


class GatePassApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.student = User.objects.create_user('student', 'student@example.com', 'password123')
        self.manager = User.objects.create_user(
            'manager', 'manager@example.com', 'password123',
            role=Role.objects.create(name='Gatepass manager', can_manage_gatepass=True),
        )
        self.payload = {
            'dno': 'D1234', 'name': 'Student Name', 'student_class': '10', 'student_section': 'A',
            'parent_email': 'parent@example.com', 'requested_date': '2026-08-01', 'reason': 'Medical appointment',
        }

    @patch('gatepass.views.send_gate_pass_submission_email.delay')
    def test_student_can_create_and_only_see_own_requests(self, send_email):
        self.client.force_authenticate(self.student)
        response = self.client.post('/api/gatepass/', self.payload, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(GatePass.objects.count(), 1)
        self.assertEqual(GatePass.objects.get().student, self.student)
        send_email.assert_called_once_with(GatePass.objects.get().id)

        other = User.objects.create_user('other', 'other@example.com', 'password123')
        GatePass.objects.create(student=other, **self.payload)
        response = self.client.get('/api/gatepass/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

    @patch('gatepass.views.send_gate_pass_decision_email.delay')
    def test_only_manager_can_approve_or_deny(self, send_email):
        gatepass = GatePass.objects.create(student=self.student, **self.payload)
        url = f'/api/gatepass/{gatepass.id}/approve_or_deny/'

        self.client.force_authenticate(self.student)
        self.assertEqual(self.client.post(url, {'status': 'approved'}, format='json').status_code, 403)

        self.client.force_authenticate(self.manager)
        response = self.client.post(url, {'status': 'approved', 'note': 'Approved'}, format='json')
        self.assertEqual(response.status_code, 200)
        gatepass.refresh_from_db()
        self.assertEqual(gatepass.status, 'approved')
        self.assertEqual(gatepass.approved_by, self.manager)
        self.assertIsNotNone(gatepass.approval_timestamp)
        send_email.assert_called_once_with(gatepass.id)
