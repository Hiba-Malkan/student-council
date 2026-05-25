"""
notifications/tasks.py

Celery tasks for all email notifications.
Schedule via Celery Beat (example at bottom of file).
"""
import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from accounts.models import User
from meetings.models import Meeting
from duty_roster.models import Duty
from competitions.models import Competition
from discipline.models import DisciplineRecord

from .models import Notification, NotificationPreference
from .utils import (
    send_notification_email,
    send_meeting_today_email,
    send_duty_today_email,
    send_competition_deadline_email,
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
    """Create MEETING_TODAY notifications for all today's meetings."""
    today = timezone.now().date()
    meetings = Meeting.objects.filter(date=today, is_cancelled=False).prefetch_related('attendees')
    created = 0

    for meeting in meetings:
        if getattr(meeting, 'morning_reminder_sent', False):
            continue
        attendees = list(meeting.attendees.filter(is_active=True))
        send_meeting_today_email(meeting, attendees)

        # Persist in-app notifications
        for attendee in attendees:
            Notification.objects.get_or_create(
                recipient=attendee,
                notification_type='MEETING_TODAY',
                defaults=dict(
                    title=f"Meeting Today: {meeting.title}",
                    message=(
                        f"You have a meeting today: {meeting.title}\n"
                        f"Time: {getattr(meeting,'time','TBD')}\n"
                        f"Location: {meeting.location or 'TBD'}"
                    ),
                    action_url=f"/meetings/{meeting.id}/",
                    send_email=False,   # already sent directly above
                    email_sent=True,
                )
            )
            created += 1

        # Mark so Beat doesn't re-fire if task runs twice
        if hasattr(meeting, 'morning_reminder_sent'):
            Meeting.objects.filter(pk=meeting.pk).update(morning_reminder_sent=True)

    return f"Meeting reminders sent for {created} attendees"


# ---------------------------------------------------------------------------
# Duty today reminders  (run ~7 AM daily)
# ---------------------------------------------------------------------------

@shared_task
def send_duty_reminders():
    """Send duty-today email to each person on duty today."""
    today = timezone.now().date()
    duties = Duty.objects.filter(date=today, is_completed=False).select_related('assigned_to')
    sent = 0

    for duty in duties:
        if not duty.assigned_to or not duty.assigned_to.email:
            continue
        send_duty_today_email(duty)

        Notification.objects.get_or_create(
            recipient=duty.assigned_to,
            notification_type='DUTY_TODAY',
            defaults=dict(
                title=f"Duty Today: {duty.duty_type_name}",
                message=(
                    f"You have {duty.duty_type_name} duty today.\n"
                    f"Location: {duty.location or 'TBD'}"
                ),
                action_url="/duty-roster/",
                send_email=False,
                email_sent=True,
            )
        )
        sent += 1

    return f"Duty reminders sent to {sent} members"


# ---------------------------------------------------------------------------
# Competition deadline reminders  (run daily)
# ---------------------------------------------------------------------------

@shared_task
def send_competition_deadline_reminders():
    """Remind council members 7, 3, and 1 day before a competition's event date."""
    today = timezone.now().date()
    remind_days = [7, 3, 1]
    created = 0

    for days in remind_days:
        target_date = today + timedelta(days=days)
        competitions = Competition.objects.filter(event_date=target_date, is_active=True)

        for comp in competitions:
            recipients = list(User.objects.filter(is_active=True, role__isnull=False))
            send_competition_deadline_email(comp, days, recipients)

            for user in recipients:
                Notification.objects.get_or_create(
                    recipient=user,
                    notification_type='COMPETITION_DEADLINE',
                    defaults=dict(
                        title=f"⏰ Competition in {days} day{'s' if days > 1 else ''}: {comp.name}",
                        message=f"{comp.name} is on {comp.event_date.strftime('%B %d')}. {days} day{'s' if days > 1 else ''} left!",
                        action_url="/competitions/",
                        send_email=False,
                        email_sent=True,
                    )
                )
                created += 1

    return f"Competition deadline notifications created: {created}"


# ---------------------------------------------------------------------------
# Daily discipline report  (run ~6 PM or end-of-day)
# ---------------------------------------------------------------------------

@shared_task
def send_daily_discipline_report_task():
    """
    Send a summary of students with 3+ offenses who had activity yesterday
    to all phase heads.
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
        send_duty_reminders(),
        send_competition_deadline_reminders(),
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
