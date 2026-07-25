from datetime import date, timedelta

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Role, User
from .models import Meeting, MinutesOfMeeting


class MeetingApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.scheduler = User.objects.create_user(
            'scheduler', 'scheduler@example.com', 'password123',
            role=Role.objects.create(name='Scheduler', can_schedule_meetings=True),
        )
        self.member = User.objects.create_user('member', 'member@example.com', 'password123')
        self.client.force_authenticate(self.scheduler)

    def test_scheduler_creates_meeting_and_mom_lifecycle(self):
        response = self.client.post('/api/meetings/', {
            'title': 'Planning', 'date': str(date.today() + timedelta(days=2)), 'location': 'Library',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        meeting = Meeting.objects.get()
        self.assertEqual(meeting.organized_by, self.scheduler)
        url = f'/api/meetings/{meeting.id}/mom/'
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, {'content': 'Discussed plans'}, format='json').status_code, 201)
        self.assertTrue(MinutesOfMeeting.objects.filter(meeting=meeting).exists())
        self.assertEqual(self.client.post(url, {'content': 'Duplicate'}, format='json').status_code, 400)
        self.assertEqual(self.client.delete(url).status_code, 204)

    def test_only_organizer_or_staff_can_edit_future_and_no_one_can_edit_past(self):
        future = Meeting.objects.create(title='Future', date=date.today() + timedelta(days=1), location='Hall', organized_by=self.scheduler)
        past = Meeting.objects.create(title='Past', date=date.today() - timedelta(days=1), location='Hall', organized_by=self.scheduler)
        self.client.force_authenticate(self.member)
        self.assertEqual(self.client.patch(f'/api/meetings/{future.id}/', {'title': 'Changed'}, format='json').status_code, 403)
        self.client.force_authenticate(self.scheduler)
        self.assertEqual(self.client.patch(f'/api/meetings/{past.id}/', {'title': 'Changed'}, format='json').status_code, 403)
        self.assertEqual(self.client.patch(f'/api/meetings/{future.id}/', {'title': 'Changed'}, format='json').status_code, 200)

    def test_list_filters_by_date_range(self):
        Meeting.objects.create(title='Soon', date=date.today() + timedelta(days=1), location='Hall')
        Meeting.objects.create(title='Later', date=date.today() + timedelta(days=10), location='Hall')
        response = self.client.get(f'/api/meetings/?date__gte={date.today()}&date__lt={date.today() + timedelta(days=5)}')
        self.assertEqual([row['title'] for row in response.data['results']], ['Soon'])
