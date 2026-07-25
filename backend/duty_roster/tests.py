from datetime import date, timedelta

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Role, User
from .models import Duty, DutyType


class DutyApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(
            'captain', 'captain@example.com', 'password123', role=Role.objects.create(name='Captain')
        )
        self.visible_user = User.objects.create_user(
            'visible', 'visible@example.com', 'password123',
            role=Role.objects.create(name='Visible student', show_in_duty_roster=True),
        )
        self.hidden_user = User.objects.create_user(
            'hidden', 'hidden@example.com', 'password123',
            role=Role.objects.create(name='Hidden student', show_in_duty_roster=False),
        )
        self.morning = DutyType.objects.create(name='Morning', location='Gate')
        self.lunch = DutyType.objects.create(name='Lunch', location='Cafeteria')
        self.client.force_authenticate(self.manager)

    def test_create_rejects_assignee_not_visible_in_roster(self):
        response = self.client.post('/api/duty-roster/duties/', {
            'assigned_to': self.hidden_user.id,
            'date': str(date.today()),
            'duty_type_name': 'Morning',
        }, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Duty.objects.count(), 0)

    def test_create_assigns_first_duty_type_and_its_location(self):
        response = self.client.post('/api/duty-roster/duties/', {
            'assigned_to': self.visible_user.id,
            'date': str(date.today()),
        }, format='json')

        self.assertEqual(response.status_code, 201)
        duty = Duty.objects.get()
        self.assertEqual(duty.duty_type, self.lunch if self.lunch.name < self.morning.name else self.morning)
        self.assertEqual(duty.location, duty.duty_type.location)
        self.assertEqual(duty.assigned_by, self.manager)

    def test_mark_complete_is_limited_to_assignee_or_c_suite(self):
        duty = Duty.objects.create(
            duty_type=self.morning, duty_type_name='Morning', assigned_to=self.visible_user, date=date.today()
        )

        response = self.client.post(f'/api/duty-roster/duties/{duty.id}/mark_complete/', {}, format='json')
        self.assertEqual(response.status_code, 403)

        self.client.force_authenticate(self.visible_user)
        response = self.client.post(
            f'/api/duty-roster/duties/{duty.id}/mark_complete/', {'notes': 'Completed'}, format='json'
        )
        self.assertEqual(response.status_code, 200)
        duty.refresh_from_db()
        self.assertTrue(duty.is_completed)
        self.assertEqual(duty.notes, 'Completed')

    def test_standard_users_only_see_their_own_duties(self):
        Duty.objects.create(duty_type_name='Morning', assigned_to=self.visible_user, date=date.today())
        Duty.objects.create(duty_type_name='Lunch', assigned_to=self.hidden_user, date=date.today() + timedelta(days=1))

        self.client.force_authenticate(self.visible_user)
        response = self.client.get('/api/duty-roster/duties/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['assigned_to'], self.visible_user.id)
