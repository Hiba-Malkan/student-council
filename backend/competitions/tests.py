from django.test import TestCase
from rest_framework.test import APIClient

from .models import Competition, CompetitionSignup


class CompetitionApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.competition = Competition.objects.create(
            name='Hackathon', hosted_by='Council, CS Club', participants='Ada, Grace', is_active=True
        )

    def test_list_helpers_and_stats_count_participants(self):
        Competition.objects.create(name='Inactive', hosted_by='Council', is_active=False)

        self.assertEqual(self.competition.hosts_list, ['Council', 'CS Club'])
        self.assertEqual(self.competition.participants_list, ['Ada', 'Grace'])
        response = self.client.get('/api/competitions/stats/')
        self.assertEqual(response.status_code, 401)

    def test_public_signup_creates_then_updates_one_signup_per_email(self):
        url = f'/api/competitions/{self.competition.id}/signup/'
        response = self.client.post(url, {'student_name': 'Sam', 'email': 'sam@example.com'}, format='json')
        self.assertEqual(response.status_code, 201)

        response = self.client.post(url, {
            'student_name': 'Samira', 'email': 'sam@example.com', 'team_name': 'The Builders'
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(CompetitionSignup.objects.count(), 1)
        self.assertEqual(CompetitionSignup.objects.get().team_name, 'The Builders')

    def test_public_signup_rejects_inactive_competition_and_invalid_email(self):
        url = f'/api/competitions/{self.competition.id}/signup/'
        self.assertEqual(self.client.post(url, {'student_name': 'Sam', 'email': 'not-an-email'}, format='json').status_code, 400)

        self.competition.is_active = False
        self.competition.save()
        self.assertEqual(self.client.post(url, {'student_name': 'Sam', 'email': 'sam@example.com'}, format='json').status_code, 400)
