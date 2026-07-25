from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import Role, User
from announcements.models import Announcement
from competitions.models import Competition
from discipline.models import DisciplineRecord, OffenseLog
from duty_roster.models import Duty
from meetings.models import Meeting
from . import tasks, utils
from .models import Notification, NotificationPreference


class NotificationEmailTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('sam', 'sam@example.com', 'password123', first_name='Sam')
        self.phase_head = User.objects.create_user(
            'head', 'head@example.com', 'password123', first_name='Head', is_phase_head=True
        )
        self.meeting = Meeting.objects.create(title='Council meeting', date=date.today(), location='Hall')
        self.announcement = Announcement.objects.create(
            title='Important update', content='x' * 310, announcement_type='URGENT', is_public=True
        )
        self.competition = Competition.objects.create(
            name='Hackathon', hosted_by='Council', event_date=date.today() + timedelta(days=3)
        )
        self.duty = Duty.objects.create(
            duty_type_name='Morning', assigned_to=self.user, date=date.today(), location='Gate', subsidiary_area='A'
        )
        self.record = DisciplineRecord.objects.create(
            student_name='Alex', class_section='10A', dno='D1234', offense_count=3
        )
        self.log = OffenseLog.objects.create(record=self.record, category='LATE', reason='Late again')

    def test_email_layout_and_low_level_sender_handle_success_empty_and_failure(self):
        html = utils._html_email('#123', '!', 'Heading', 'Sub', '<p>Body</p>', '/go', 'Go')
        self.assertIn('Heading', html)
        self.assertIn('href="/go"', html)
        self.assertIn('Label:', utils._detail_box('#123', [('Label', 'Value')]))
        self.assertFalse(utils._send('subject', html, []))
        with patch('notifications.utils.EmailMultiAlternatives') as email:
            self.assertTrue(utils._send('subject', html, 'sam@example.com'))
            email.return_value.attach_alternative.assert_called_once()
            email.return_value.send.assert_called_once()
            email.return_value.reset_mock()
            email.return_value.send.side_effect = RuntimeError('smtp down')
            self.assertFalse(utils._send('subject', html, ['sam@example.com', '']))

    @patch('notifications.utils._send')
    def test_all_typed_email_builders_send_expected_recipients(self, send):
        self.meeting.description = 'Bring reports'
        self.meeting.cancellation_reason = 'Weather'
        utils.send_meeting_scheduled_email(self.meeting, [self.user])
        utils.send_meeting_today_email(self.meeting, [self.user])
        utils.send_meeting_cancelled_email(self.meeting, [self.user])
        utils.send_duty_today_email(self.duty)
        utils.send_announcement_new_email(self.announcement, [self.user])
        utils.send_announcement_important_email(self.announcement, [self.user])
        utils.send_competition_new_email(self.competition, [self.user])
        utils.send_competition_deadline_email(self.competition, 1, [self.user])
        utils.send_discipline_warning_email(self.record, self.log)
        utils.send_daily_discipline_report([self.record], date.today())

        recipients = [call.args[-1] for call in send.call_args_list]
        self.assertIn(self.user.email, recipients)
        self.assertIn(self.phase_head.email, recipients)
        self.assertGreaterEqual(send.call_count, 10)

    @patch('notifications.utils._send')
    def test_gatepass_submission_and_decision_email_reach_all_recipients(self, send):
        gatepass = SimpleNamespace(
            student=self.user, name='Sam', dno='D123', student_class='10', student_section='A',
            requested_date=date.today(), reason='Appointment', parent_email='parent@example.com',
            ct_email='teacher1@example.com, teacher2@example.com', status='approved',
            approved_by=self.phase_head, approval_note='Fine', approval_timestamp=timezone.now(),
        )
        utils.send_gatepass_submitted_email(gatepass)
        self.assertEqual(send.call_count, 5)  # student, parent, two teachers, phase head
        send.reset_mock()
        utils.send_gatepass_decision_email(gatepass)
        self.assertEqual(send.call_count, 4)  # student, parent, two teachers

    @patch('notifications.utils._dispatch_notification_email')
    def test_generic_notification_marks_successful_email_sent(self, dispatch):
        notification = Notification.objects.create(
            recipient=self.user, notification_type='GENERAL', title='Hello', message='World', send_email=True
        )
        self.assertTrue(utils.send_notification_email(notification))
        notification.refresh_from_db()
        self.assertTrue(notification.email_sent)
        self.assertIsNotNone(notification.email_sent_at)
        dispatch.assert_called_once_with(notification)
        self.assertFalse(utils.send_notification_email(notification))

    @patch('notifications.utils._send')
    def test_generic_dispatch_and_email_failures_are_safe(self, send):
        notification = Notification.objects.create(
            recipient=self.user, notification_type='GENERAL', title='Hello', message='World',
            action_url='/notifications/', send_email=True,
        )
        utils._dispatch_notification_email(notification)
        send.assert_called_once()
        with patch('notifications.utils._dispatch_notification_email', side_effect=RuntimeError('broken')):
            self.assertFalse(utils.send_notification_email(notification))


class NotificationTaskAndApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('sam', 'sam@example.com', 'password123')
        self.client.force_authenticate(self.user)

    def test_notification_api_hides_snoozed_marks_and_clears_only_current_user_items(self):
        unread = Notification.objects.create(recipient=self.user, notification_type='GENERAL', title='One', message='one')
        snoozed = Notification.objects.create(
            recipient=self.user, notification_type='GENERAL', title='Two', message='two', is_snoozed=True,
            snoozed_until=timezone.now() + timedelta(hours=1),
        )
        other = User.objects.create_user('other', 'other@example.com', 'password123')
        Notification.objects.create(recipient=other, notification_type='GENERAL', title='Other', message='other', is_read=True)

        self.assertEqual(self.client.get('/api/notifications/unread_count/').data['count'], 1)
        self.assertEqual(self.client.post(f'/api/notifications/{unread.id}/mark_read/', {}, format='json').status_code, 200)
        self.assertEqual(self.client.post(f'/api/notifications/{snoozed.id}/unsnooze/', {}, format='json').status_code, 200)
        self.assertEqual(self.client.post('/api/notifications/mark_all_read/', {}, format='json').data['marked_read'], 1)
        self.assertEqual(self.client.delete('/api/notifications/clear_read/').data['deleted'], 2)
        self.assertEqual(Notification.objects.filter(recipient=other).count(), 1)

    @patch('notifications.tasks.send_notification_email')
    def test_pending_email_task_counts_sent_skipped_and_failed(self, sender):
        eligible = Notification.objects.create(recipient=self.user, notification_type='GENERAL', title='A', message='A', send_email=True)
        opted_out = Notification.objects.create(recipient=self.user, notification_type='MEETING_TODAY', title='B', message='B', send_email=True)
        failed = Notification.objects.create(recipient=self.user, notification_type='GENERAL', title='C', message='C', send_email=True)
        NotificationPreference.objects.create(user=self.user, email_for_meetings=False)
        sender.side_effect = [True, False]

        result = tasks.send_pending_email_notifications()
        opted_out.refresh_from_db()
        self.assertEqual(result, 'Sent 1 | Skipped 1 | Failed 1')
        self.assertTrue(opted_out.email_sent)
        self.assertEqual(sender.call_count, 2)

    @patch('notifications.tasks.send_duty_today_email')
    def test_duty_reminder_task_creates_one_notification_and_skips_completed(self, send):
        Duty.objects.create(duty_type_name='Morning', assigned_to=self.user, date=date.today())
        Duty.objects.create(duty_type_name='Done', assigned_to=self.user, date=date.today(), is_completed=True)

        self.assertEqual(tasks.send_duty_reminders(), 'Duty reminders sent to 1 members')
        self.assertTrue(Notification.objects.filter(recipient=self.user, notification_type='DUTY_TODAY').exists())
        send.assert_called_once()

    @patch('notifications.tasks.send_meeting_today_email')
    def test_meeting_reminder_task_notifies_active_attendees_once(self, send):
        meeting = Meeting.objects.create(title='Today', date=date.today(), location='Hall')
        meeting.attendees.add(self.user)

        self.assertEqual(tasks.send_morning_meeting_reminders(), 'Meeting reminders sent for 1 attendees')
        self.assertTrue(Notification.objects.filter(recipient=self.user, notification_type='MEETING_TODAY').exists())
        meeting.refresh_from_db()
        self.assertTrue(meeting.morning_reminder_sent)
        self.assertEqual(tasks.send_morning_meeting_reminders(), 'Meeting reminders sent for 0 attendees')
        send.assert_called_once()

    @patch('notifications.tasks.send_competition_deadline_email')
    def test_competition_deadline_task_and_cleanup(self, send):
        council_user = User.objects.create_user(
            'council', 'council@example.com', 'password123', role=Role.objects.create(name='Member')
        )
        Competition.objects.create(name='Soon', hosted_by='Council', event_date=date.today() + timedelta(days=3))
        old = Notification.objects.create(
            recipient=self.user, notification_type='GENERAL', title='Old', message='old', is_read=True,
            read_at=timezone.now() - timedelta(days=31),
        )

        self.assertEqual(tasks.send_competition_deadline_reminders(), 'Competition deadline notifications created: 1')
        self.assertTrue(Notification.objects.filter(recipient=council_user, notification_type='COMPETITION_DEADLINE').exists())
        self.assertEqual(tasks.cleanup_old_notifications(), 'Deleted 1 old notifications')
        self.assertFalse(Notification.objects.filter(id=old.id).exists())
        send.assert_called_once()

    @patch('notifications.tasks.send_pending_email_notifications', return_value='pending')
    @patch('notifications.tasks.send_competition_deadline_reminders', return_value='competition')
    @patch('notifications.tasks.send_duty_reminders', return_value='duty')
    @patch('notifications.tasks.send_morning_meeting_reminders', return_value='meeting')
    def test_daily_notification_task_combines_subtask_results(self, *_mocks):
        self.assertEqual(tasks.send_daily_notifications(), 'meeting | duty | competition | pending')
