import re
from datetime import date, datetime, timedelta

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from meetings.models import Meeting
from duty_roster.models import Duty
from announcements.models import Announcement
from competitions.models import Competition
from accounts.models import User

from .models import Notification
from .utils import (
    send_meeting_scheduled_email,
    send_announcement_new_email,
    send_announcement_important_email,
    send_competition_new_email,
)


# ---------------------------------------------------------------------------
# Meetings
# ---------------------------------------------------------------------------

@receiver(post_save, sender=Meeting)
def on_meeting_save(sender, instance, created, **kwargs):
    if not created:
        return

    council = list(User.objects.filter(is_active=True).select_related('role'))
    send_meeting_scheduled_email(instance, council)


# ---------------------------------------------------------------------------
# Duties — one queued email per assignment batch, listing all dates, grouped
# into 2-week chunks. No daily reminder notifications.
# ---------------------------------------------------------------------------

# Chunks are laid out on a fixed 14-day grid rather than anchored to the first
# date in whatever batch happens to arrive. Anchoring to arrival time made the
# window (and therefore the notification title) shift depending on WHEN duties
# were assigned, so the same date range could produce several notifications.
_CHUNK_EPOCH = date(2024, 1, 1)
_CHUNK_DAYS = 14


def _chunk_bounds(duty_date):
    """Return the (start, end) of the 14-day grid window containing duty_date."""
    start = _CHUNK_EPOCH + timedelta(days=((duty_date - _CHUNK_EPOCH).days // _CHUNK_DAYS) * _CHUNK_DAYS)
    return start, start + timedelta(days=_CHUNK_DAYS)


@receiver(post_save, sender=Duty)
def on_duty_assigned(sender, instance, created, **kwargs):
    if not created:
        return

    user = instance.assigned_to
    location = instance.location or "TBD"
    subsidiary = (f", {instance.subsidiary_area}" if getattr(instance, 'subsidiary_area', None) else "")
    instructions = getattr(instance, 'instructions', None)

    # Every duty for this person + duty type inside this window, not just the
    # ones created in the last hour. The old time-based batch window meant a
    # duty assigned the next day started a fresh chunk and emailed again.
    chunk_start, chunk_end = _chunk_bounds(instance.date)
    chunk_duties = list(Duty.objects.filter(
        assigned_to=user,
        duty_type_name=instance.duty_type_name,
        date__gte=chunk_start,
        date__lt=chunk_end,
    ).order_by('date'))

    if not chunk_duties:
        return

    # Stable title keyed on the fixed window start, so every duty landing in
    # this window updates the SAME notification.
    title = f"Duty Assigned — {instance.duty_type_name} (from {chunk_start.strftime('%B %d, %Y')})"
    dates = [d.date for d in chunk_duties]

    existing = Notification.objects.filter(
        recipient=user,
        notification_type='DUTY_ASSIGNED',
        title=title,
    )

    # Dates this recipient has already been told about in this window. If the
    # email already went out and covers every date, there is nothing to say —
    # creating a row here is what produced thousands of unread no-ops.
    already_covered = set()
    pending = None
    for notification in existing:
        if not notification.email_sent:
            if pending is None:
                pending = notification
            continue
        for covered in re.findall(r'[A-Z][a-z]+ \d{2}, \d{4}', notification.message):
            try:
                already_covered.add(datetime.strptime(covered, '%B %d, %Y').date())
            except ValueError:
                continue

    if pending is None and all(d in already_covered for d in dates):
        return

    notification = pending or Notification.objects.create(
        recipient=user,
        notification_type='DUTY_ASSIGNED',
        title=title,
        message="",
        action_url="/duty-roster/",
        send_email=True,
    )

    if len(chunk_duties) > 1:
        dates_str = ", ".join(d.strftime("%B %d, %Y") for d in dates)
        message = (
            f"You have been assigned {instance.duty_type_name} duty on "
            f"the following dates:\n{dates_str}\n"
            f"Location: {location}{subsidiary}"
        )
    else:
        message = (
            f"You have been assigned {instance.duty_type_name} duty on "
            f'{dates[0].strftime("%B %d, %Y")}.\n'
            f"Location: {location}{subsidiary}"
        )
    if instructions:
        message += f"\n\nInstructions:\n{instructions}"

    notification.message = message
    notification.save(update_fields=['message'])


# ---------------------------------------------------------------------------
# Announcements
# ---------------------------------------------------------------------------

@receiver(post_save, sender=Announcement)
def on_announcement_created(sender, instance, created, **kwargs):
    if not created:
        return

    is_urgent = getattr(instance, 'announcement_type', '') == 'URGENT'

    # Resolve recipients
    recipients = set()
    for role in instance.target_roles.all():
        recipients.update(role.users.filter(is_active=True))
    recipients.update(instance.target_users.filter(is_active=True))
    if instance.is_public:
        recipients.update(User.objects.filter(is_active=True))

    recipients_list = list(recipients)
    if is_urgent:
        send_announcement_important_email(instance, recipients_list)
    elif instance.is_public:
        # Urgent and public posts are emailed; role/user-targeted posts are not
        send_announcement_new_email(instance, recipients_list)


# ---------------------------------------------------------------------------
# Competitions
# ---------------------------------------------------------------------------

@receiver(post_save, sender=Competition)
def on_competition_created(sender, instance, created, **kwargs):
    if not created:
        return

    # New competitions go to everyone
    members = list(User.objects.filter(is_active=True).select_related('role'))
    send_competition_new_email(instance, members)
