from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

from meetings.models import Meeting
from duty_roster.models import Duty
from announcements.models import Announcement
from competitions.models import Competition
from discipline.models import DisciplineRecord, OffenseLog
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
    council = list(User.objects.filter(is_active=True).select_related('role'))

    if created:
        # In-app notifications
        for member in council:
            Notification.objects.create(
                recipient=member,
                notification_type='MEETING_TODAY',
                title=f"Meeting Scheduled: {instance.title}",
                message=(
                    f'A new meeting "{instance.title}" has been scheduled for '
                    f'{instance.date.strftime("%B %d, %Y")} at {instance.location or "TBD"}.'
                ),
                action_url=f"/meetings/{instance.id}/",
                send_email=False,   # typed email sent directly below
            )
        # Direct typed email
        send_meeting_scheduled_email(instance, council)


# ---------------------------------------------------------------------------
# Duties — one notification (in-app + email) per assignment batch, listing all
# dates, grouped into 2-week chunks. No daily reminder notifications.
# ---------------------------------------------------------------------------

@receiver(post_save, sender=Duty)
def on_duty_assigned(sender, instance, created, **kwargs):
    if not created:
        return

    user = instance.assigned_to
    location = instance.location or "TBD"
    subsidiary = (f", {instance.subsidiary_area}" if getattr(instance, 'subsidiary_area', None) else "")
    instructions = getattr(instance, 'instructions', None)

    # Gather the whole assignment batch for this person + duty type
    batch = list(Duty.objects.filter(
        assigned_to=user,
        duty_type_name=instance.duty_type_name,
        created_at__gte=timezone.now() - timedelta(hours=1),
    ).order_by('date'))

    if not batch:
        return

    # Group the batch into 2-week chunks measured from the first assigned date.
    # Each chunk becomes its own email so a single email never spans >2 weeks.
    anchor = batch[0].date
    chunks = {}
    for duty in batch:
        index = (duty.date - anchor).days // 14
        chunks.setdefault(index, []).append(duty)

    for index, chunk_duties in chunks.items():
        chunk_duties.sort(key=lambda d: d.date)
        first = chunk_duties[0].date

        # Stable title keyed on the 2-week window start so every duty added to
        # this chunk updates the SAME pending email (no duplicate emails).
        chunk_start = anchor + timedelta(days=index * 14)
        title = f"Duty Assigned — {instance.duty_type_name} (from {chunk_start.strftime('%B %d, %Y')})"
        pending = Notification.objects.filter(
            recipient=user,
            notification_type='DUTY_ASSIGNED',
            title=title,
            send_email=True,
            email_sent=False,
        ).first()
        notification = pending or Notification.objects.create(
            recipient=user,
            notification_type='DUTY_ASSIGNED',
            title=title,
            message="",
            action_url="/duty-roster/",
            send_email=True,
        )

        if len(chunk_duties) > 1:
            dates_str = ", ".join(d.date.strftime("%B %d, %Y") for d in chunk_duties)
            message = (
                f"You have been assigned {instance.duty_type_name} duty on "
                f"the following dates:\n{dates_str}\n"
                f"Location: {location}{subsidiary}"
            )
        else:
            message = (
                f"You have been assigned {instance.duty_type_name} duty on "
                f'{first.strftime("%B %d, %Y")}.\n'
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
    notif_type = 'ANNOUNCEMENT_IMPORTANT' if is_urgent else 'ANNOUNCEMENT_NEW'

    # Resolve recipients
    recipients = set()
    for role in instance.target_roles.all():
        recipients.update(role.users.filter(is_active=True))
    recipients.update(instance.target_users.filter(is_active=True))
    if instance.is_public:
        recipients.update(User.objects.filter(is_active=True))

    prefix = "🚨 URGENT: " if is_urgent else ""
    for user in recipients:
        Notification.objects.create(
            recipient=user,
            notification_type=notif_type,
            title=f"{prefix}{instance.title}",
            message=(instance.content or "")[:200] + ("…" if len(instance.content or "") > 200 else ""),
            action_url="/announcements/",
            send_email=False,   # typed email sent below
        )

    recipients_list = list(recipients)
    if is_urgent:
        send_announcement_important_email(instance, recipients_list)
    else:
        # Only email for public or explicitly urgent; in-app only for targeted
        if instance.is_public:
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

    for member in members:
        Notification.objects.create(
            recipient=member,
            notification_type='COMPETITION_NEW',
            title=f"New Competition: {instance.name}",
            message=f'"{instance.name}" hosted by {instance.hosted_by} has been announced!',
            action_url="/competitions/",
            send_email=False,   # typed email sent below
        )

    send_competition_new_email(instance, members)


# ---------------------------------------------------------------------------
# Discipline — 3+ offense warning to phase heads
# ---------------------------------------------------------------------------

@receiver(post_save, sender=OffenseLog)
def on_offense_log_created(sender, instance, created, **kwargs):
    if not created:
        return

    record = instance.record

    # Always create a notification for discipline managers
    discipline_managers = User.objects.filter(
        role__can_record_discipline=True, is_active=True
    )
    phase_heads = User.objects.filter(is_phase_head=True, is_active=True)
    alert_recipients = set(discipline_managers) | set(phase_heads)

    if record.offense_count >= 3:
        for recipient in alert_recipients:
            Notification.objects.create(
                recipient=recipient,
                notification_type='DISCIPLINE_WARNING',
                title=f"⚠️ Discipline Alert: {record.student_name}",
                message=(
                    f"{record.student_name} (Class {record.class_section}, DNO: {record.dno}) "
                    f"has reached {record.offense_count} offenses. "
                    f"Latest: {instance.get_category_display()}"
                ),
                action_url=f"/discipline/{record.id}/",
                send_email=False,   # no per-offense emails; only the daily report is emailed
            )