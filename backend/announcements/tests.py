from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Role, User
from .models import Announcement, AnnouncementRead, EventParticipant


class AnnouncementApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.c_suite = User.objects.create_user(
            'president', 'president@example.com', 'password123', role=Role.objects.create(name='President')
        )
        self.student = User.objects.create_user('student', 'student@example.com', 'password123', house='A', grade='10')
        self.other = User.objects.create_user('other', 'other@example.com', 'password123', house='B', grade='11')
        self.public = Announcement.objects.create(title='Public', content='For everyone', is_public=True)
        self.house_a = Announcement.objects.create(title='House A', content='For A', target_houses='A')
        self.hidden = Announcement.objects.create(title='Hidden', content='For nobody', is_published=False)

    def test_targeted_list_unread_and_mark_read_only_show_allowed_announcements(self):
        self.client.force_authenticate(self.student)
        response = self.client.get('/api/announcements/')
        titles = {row['title'] for row in response.data['results']}
        self.assertEqual(titles, {'Public', 'House A'})

        self.client.post(f'/api/announcements/{self.public.id}/mark_read/', {}, format='json')
        self.assertTrue(AnnouncementRead.objects.filter(announcement=self.public, user=self.student).exists())
        response = self.client.get('/api/announcements/unread/')
        self.assertEqual([row['title'] for row in response.data], ['House A'])

    def test_only_c_suite_can_create_pin_and_delete_announcements(self):
        self.client.force_authenticate(self.student)
        response = self.client.post('/api/announcements/', {'title': 'Nope', 'content': 'No permission'}, format='json')
        self.assertEqual(response.status_code, 403)

        self.client.force_authenticate(self.c_suite)
        response = self.client.post('/api/announcements/', {
            'title': 'Created', 'content': 'Created by council', 'is_public': True,
        }, format='json')
        self.assertEqual(response.status_code, 201)
        announcement = Announcement.objects.get(title='Created')
        self.assertEqual(announcement.created_by, self.c_suite)
        self.assertIsNotNone(announcement.published_at)
        self.assertFalse(announcement.is_pinned)
        self.assertTrue(self.client.post(f'/api/announcements/{announcement.id}/pin/', {}, format='json').data['is_pinned'])
        self.assertEqual(self.client.delete(f'/api/announcements/{announcement.id}/').status_code, 204)

    def test_public_endpoint_shows_only_public_published_items(self):
        response = self.client.get('/api/announcements/public/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row['title'] for row in response.data['results']], ['Public'])

    def test_event_participants_register_themselves_and_captain_confirms_attendance(self):
        event = Announcement.objects.create(title='Event', content='Event details', announcement_type='EVENT', is_public=True)
        self.client.force_authenticate(self.student)
        response = self.client.post('/api/announcements/participants/', {
            'announcement': event.id, 'role_in_event': 'Performer',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        participant = EventParticipant.objects.get()
        self.assertEqual(participant.user, self.student)

        self.assertEqual(self.client.post(f'/api/announcements/participants/{participant.id}/confirm/', {}, format='json').status_code, 403)
        self.client.force_authenticate(self.c_suite)
        self.assertEqual(self.client.post(f'/api/announcements/participants/{participant.id}/confirm/', {}, format='json').data['status'], 'CONFIRMED')
        self.assertEqual(self.client.post(
            f'/api/announcements/participants/{participant.id}/mark_attendance/', {'attended': False}, format='json'
        ).data['status'], 'ABSENT')
