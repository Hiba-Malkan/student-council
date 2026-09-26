"""
notifications/tasks.py

Celery tasks for all email notifications.
Schedule via Celery Beat (example at bottom of file).
"""
import logging
from celery import shared_task
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from accounts.models import User
from meetings.models import Meeting
from discipline.models import DisciplineRecord

from .models import Notification, NotificationPreference
from .utils import (
    send_notification_email,
    send_meeting_today_email,
    send_daily_discipline_report,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Gate pass tasks (imported by gatepass/tasks.py)
# These live here so everything email-related is in one app.
# ---------------------------------------------------------------------------

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_gate_pass_submission_email(self, gatepass_id):
    """Send submission emails (student + parent + CT + phase heads)."""
    try:
        from gatepass.models import GatePass
        from .utils import send_gatepass_submitted_email
        gatepass = GatePass.objects.select_related('student', 'approved_by').get(id=gatepass_id)
        send_gatepass_submitted_email(gatepass)
    except Exception as exc:
        logger.error(f"send_gate_pass_submission_email failed for #{gatepass_id}: {exc}", exc_info=True)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_gate_pass_decision_email(self, gatepass_id):
    """Send approved/denied emails (student + parent + CT)."""
    try:
        from gatepass.models import GatePass
        from .utils import send_gatepass_decision_email
        gatepass = GatePass.objects.select_related('student', 'approved_by').get(id=gatepass_id)
        send_gatepass_decision_email(gatepass)
    except Exception as exc:
        logger.error(f"send_gate_pass_decision_email failed for #{gatepass_id}: {exc}", exc_info=True)
        raise self.retry(exc=exc)


# ---------------------------------------------------------------------------
# Pending notification emails  (generic queue flush)
# ---------------------------------------------------------------------------

# Map notification_type → NotificationPreference field name
_PREF_MAP = {
    'MEETING_TODAY':          'email_for_meetings',
    'MEETING_MORNING':        'email_for_meetings',
    'MEETING_10MIN':          'email_for_meetings',
    'MEETING_CANCELLED':      'email_for_meetings',
    'MEETING_RESCHEDULED':    'email_for_meetings',
    'DUTY_TODAY':             'email_for_duties',
    'DUTY_ASSIGNED':          'email_for_duties',
    'DUTY_MORNING':           'email_for_duties',
    'ANNOUNCEMENT_NEW':       'email_for_announcements',
    'ANNOUNCEMENT_IMPORTANT': 'email_for_announcements',
    'COMPETITION_NEW':        'email_for_competitions',  # field added below
    'COMPETITION_DEADLINE':   'email_for_competitions',
    'COMPETITION_STARTING':   'email_for_competitions',
    'DISCIPLINE_WARNING':     'email_for_discipline',
    'DISCIPLINE_DAILY_REPORT':'email_for_discipline',
    'DISCIPLINE_NEW_OFFENSE': 'email_for_discipline',
}


@shared_task
def send_pending_email_notifications():
    """Flush all Notification objects that are queued for email but not yet sent."""
    pending = Notification.objects.filter(
        send_email=True,
        email_sent=False,
    ).select_related('recipient')

    sent = skipped = failed = 0

    for notif in pending:
        # Honour user preferences
        pref_field = _PREF_MAP.get(notif.notification_type)
        if pref_field:
            prefs = NotificationPreference.objects.filter(user=notif.recipient).first()
            if prefs and not getattr(prefs, pref_field, True):
                # User opted out — mark done so we don't re-process
                notif.email_sent = True
                notif.save(update_fields=['email_sent'])
                skipped += 1
                continue

        if send_notification_email(notif):
            sent += 1
        else:
            failed += 1

    return f"Sent {sent} | Skipped {skipped} | Failed {failed}"


# ---------------------------------------------------------------------------
# Meeting today reminders  (run ~7 AM daily)
# ---------------------------------------------------------------------------

@shared_task
def send_morning_meeting_reminders():
    """Email the morning meeting reminder to all of today's meetings' attendees."""
    today = timezone.now().date()
    meetings = Meeting.objects.filter(date=today, is_cancelled=False)

    # Council members = users marked visible in the duty roster
    council = list(User.objects.filter(is_active=True).filter(
        Q(show_in_duty_roster=True) |
        Q(show_in_duty_roster__isnull=True, role__show_in_duty_roster=True)
    ).distinct())

    sent = 0

    for meeting in meetings:
        if getattr(meeting, 'morning_reminder_sent', False):
            continue
        send_meeting_today_email(meeting, council)
        sent += len(council)

        # Mark so Beat doesn't re-fire if task runs twice
        if hasattr(meeting, 'morning_reminder_sent'):
            Meeting.objects.filter(pk=meeting.pk).update(morning_reminder_sent=True)

    return f"Meeting reminders sent for {sent} attendees"


# ---------------------------------------------------------------------------
# Daily discipline report  (run ~6 PM or end-of-day)
# ---------------------------------------------------------------------------

@shared_task
def send_daily_discipline_report_task():
    """
    Send a summary of students with 3+ offenses who had activity yesterday
    to all phase heads and superusers.
    """
    yesterday = timezone.now().date() - timedelta(days=1)

    students = DisciplineRecord.objects.filter(
        offense_count__gte=3,
        offense_logs__created_at__date=yesterday,
    ).distinct()

    if not students.exists():
        return "No students with 3+ offenses yesterday — report skipped"

    send_daily_discipline_report(students, yesterday)
    return f"Daily discipline report sent for {students.count()} students"


# ---------------------------------------------------------------------------
# Master daily task — wire this single task in Celery Beat
# ---------------------------------------------------------------------------

@shared_task
def send_daily_notifications():
    """
    Umbrella task. Schedule via Celery Beat at 7:00 AM daily.
    Calls sub-tasks synchronously (or chain them if you prefer async).
    """
    results = [
        send_morning_meeting_reminders(),
        send_pending_email_notifications(),
    ]
    return " | ".join(results)


# ---------------------------------------------------------------------------
# Cleanup  (run weekly)
# ---------------------------------------------------------------------------

@shared_task
def cleanup_old_notifications():
    """Delete read notifications older than 30 days."""
    cutoff = timezone.now() - timedelta(days=30)
    deleted, _ = Notification.objects.filter(is_read=True, read_at__lt=cutoff).delete()
    return f"Deleted {deleted} old notifications"
