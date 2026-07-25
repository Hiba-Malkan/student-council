from django.test import TestCase
from rest_framework.test import APIClient

from .models import Club, ClubSignup


class ClubApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.club = Club.objects.create(
            name='Robotics', description='Build robots', established_year=2020,
            established_by=' Ada, Grace ,, Lin ', tutors=' Mr A, Ms B ', member_count=12,
        )

    def test_list_helpers_normalize_comma_separated_names(self):
        self.assertEqual(self.club.founders_list, ['Ada', 'Grace', 'Lin'])
        self.assertEqual(self.club.tutors_list, ['Mr A', 'Ms B'])

    def test_public_join_creates_then_updates_one_signup_per_email(self):
        url = f'/api/clubs/{self.club.id}/join/'
        response = self.client.post(url, {'student_name': 'Sam', 'email': 'sam@example.com'}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ClubSignup.objects.count(), 1)

        response = self.client.post(url, {
            'student_name': 'Samira', 'email': 'sam@example.com', 'phone': '0501234567'
        }, format='json')
        self.assertEqual(response.status_code, 201)
        signup = ClubSignup.objects.get()
        self.assertEqual(ClubSignup.objects.count(), 1)
        self.assertEqual(signup.student_name, 'Samira')
        self.assertEqual(signup.phone, '0501234567')

    def test_public_join_validates_required_name_and_email_format(self):
        url = f'/api/clubs/{self.club.id}/join/'
        self.assertEqual(self.client.post(url, {'email': 'sam@example.com'}, format='json').status_code, 400)
        self.assertEqual(self.client.post(url, {'student_name': 'Sam', 'email': 'invalid'}, format='json').status_code, 400)

    def test_stats_are_available_without_authentication(self):
        Club.objects.create(
            name='Drama', description='Perform', established_year=2021,
            established_by='Alex', tutors='Ms C', status='active', member_count=8,
        )

        response = self.client.get('/api/clubs/stats/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total_clubs'], 2)
        self.assertEqual(response.data['active_clubs'], 1)
        self.assertEqual(response.data['total_members'], 20)
