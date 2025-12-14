from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from datetime import datetime, timedelta

from meetings.models import Meeting
from duty_roster.models import Duty
from announcements.models import Announcement
from competitions.models import Competition
from discipline.models import DisciplineRecord, OffenseLog
from accounts.models import User
from .models import Notification
from .utils import send_notification_email, send_daily_discipline_report


@receiver(post_save, sender=Meeting)
def notify_meeting_created(sender, instance, created, **kwargs):
    """Send notifications when a meeting is created or updated"""
    if created:
        # Notify all council members about new meeting
        council_members = User.objects.filter(is_active=True)
        for member in council_members:
            Notification.objects.create(
                recipient=member,
                notification_type='MEETING_TODAY',
                title=f'New Meeting: {instance.title}',
                message=f'A new meeting "{instance.title}" has been scheduled for {instance.date.strftime("%B %d, %Y")} at {instance.location}.',
                action_url=f'/meetings/{instance.id}/',
                send_email=True
            )
    elif instance.is_cancelled:
        # Notify all council members about cancellation
        council_members = User.objects.filter(is_active=True)
        for member in council_members:
            Notification.objects.create(
                recipient=member,
                notification_type='MEETING_CANCELLED',
                title=f'Meeting Cancelled: {instance.title}',
                message=f'The meeting "{instance.title}" scheduled for {instance.date.strftime("%B %d, %Y")} has been cancelled. {instance.cancellation_reason}',
                action_url=f'/meetings/',
                send_email=True
            )


@receiver(post_save, sender=Duty)
def notify_duty_assigned(sender, instance, created, **kwargs):
    """Notify user when duty is assigned"""
    if created:
        # Format subject: Duty Assigned - Duty Type, Location, Subsidiary Area
        duty_location = instance.location if instance.location else "Location TBD"
        subsidiary_area = f", {instance.subsidiary_area}" if instance.subsidiary_area else ""
        
        # Build message with all details
        message = f'You have been assigned {instance.duty_type_name} duty on {instance.date.strftime("%B %d, %Y")} (Today).\n\n'
        message += f'Location: {duty_location}{subsidiary_area}'
        
        if instance.instructions:
            message += f'\n\nAdditional Instructions:\n{instance.instructions}'
        
        Notification.objects.create(
            recipient=instance.assigned_to,
            notification_type='DUTY_ASSIGNED',
            title=f'Duty Assigned - {instance.duty_type_name}, {duty_location}{subsidiary_area}',
            message=message,
            action_url='/duty-roster/',
            send_email=True
        )


@receiver(post_save, sender=Announcement)
def notify_announcement_created(sender, instance, created, **kwargs):
    """Send notifications when a new announcement is posted"""
    if created:
        notification_type = 'ANNOUNCEMENT_IMPORTANT' if instance.announcement_type == 'URGENT' else 'ANNOUNCEMENT_NEW'
        
        # Get all target users
        recipients = set()
        
        # Add users from target_roles
        for role in instance.target_roles.all():
            recipients.update(role.users.all())
        
        # Add users from target_users
        recipients.update(instance.target_users.all())
        
        # If public, notify all active users
        if instance.is_public:
            recipients.update(User.objects.filter(is_active=True))
        
        # Create notifications
        for user in recipients:
            Notification.objects.create(
                recipient=user,
                notification_type=notification_type,
                title=f'{"🚨 URGENT: " if instance.announcement_type == "URGENT" else ""}{instance.title}',
                message=instance.content[:200] + ('...' if len(instance.content) > 200 else ''),
                action_url='/announcements/',
                send_email=instance.announcement_type == 'URGENT'  # Only send email for urgent announcements
            )


@receiver(post_save, sender=Competition)
def notify_competition_created(sender, instance, created, **kwargs):
    """Notify users about new competitions"""
    if created:
        # Notify all active council members
        council_members = User.objects.filter(is_active=True, role__isnull=False)
        
        for member in council_members:
            Notification.objects.create(
                recipient=member,
                notification_type='COMPETITION_NEW',
                title=f'New Competition: {instance.name}',
                message=f'A new competition "{instance.name}" hosted by {instance.hosted_by} has been announced. Check it out!',
                action_url='/competitions/',
                send_email=False  # In-app only for competitions
            )


@receiver(post_save, sender=OffenseLog)
def notify_discipline_offense(sender, instance, created, **kwargs):
    """Notify when offense is recorded and check for 3+ offenses"""
    if created:
        record = instance.record
        
        # Check if student has reached 3 or more offenses
        if record.offense_count >= 3:
            # Notify phase heads and discipline managers
            phase_heads = User.objects.filter(is_phase_head=True)
            discipline_managers = User.objects.filter(role__can_record_discipline=True, is_staff=True)
            
            recipients = set(phase_heads) | set(discipline_managers)
            
            for recipient in recipients:
                Notification.objects.create(
                    recipient=recipient,
                    notification_type='DISCIPLINE_WARNING',
                    title=f'⚠️ Discipline Alert: {record.student_name}',
                    message=f'{record.student_name} (Class {record.class_section}, DNO: {record.dno}) has reached {record.offense_count} offenses. Latest: {instance.category_display}',
                    action_url=f'/discipline/{record.id}/',
                    send_email=True
                )


def send_daily_notifications():
    """
    Called by scheduled task to send daily notifications
    This should be run early morning (e.g., 7 AM)
    """
    today = timezone.now().date()
    
    # 1. Notify users about today's meetings
    today_meetings = Meeting.objects.filter(date=today, is_cancelled=False)
    for meeting in today_meetings:
        if not meeting.morning_reminder_sent:
            for attendee in meeting.attendees.all():
                Notification.objects.create(
                    recipient=attendee,
                    notification_type='MEETING_MORNING',
                    title=f'📅 Meeting Today: {meeting.title}',
                    message=f'Reminder: You have a meeting "{meeting.title}" today at {meeting.location}.',
                    action_url=f'/meetings/{meeting.id}/',
                    send_email=True
                )
            meeting.morning_reminder_sent = True
            meeting.save()
    
    # 2. Notify users about today's duties
    today_duties = Duty.objects.filter(date=today, is_completed=False).select_related('assigned_to')
    for duty in today_duties:
        Notification.objects.create(
            recipient=duty.assigned_to,
            notification_type='DUTY_TODAY',
            title=f'📋 Duty Today: {duty.duty_type_name}',
            message=f'Reminder: You have {duty.duty_type_name} duty today at {duty.location or "your assigned location"}.',
            action_url='/duty-roster/',
            send_email=True
        )
    
    # 3. Send discipline report to phase heads
    yesterday = today - timedelta(days=1)
    students_with_3plus = DisciplineRecord.objects.filter(
        offense_count__gte=3,
        offense_logs__created_at__date=yesterday
    ).distinct()
    
    if students_with_3plus.exists():
        send_daily_discipline_report(students_with_3plus, yesterday)


def send_competition_deadline_reminders():
    """
    Remind users about competitions happening soon
    Called by scheduled task
    """
    today = timezone.now().date()
    week_from_now = today + timedelta(days=7)
    
    upcoming_competitions = Competition.objects.filter(
        event_date__gte=today,
        event_date__lte=week_from_now,
        is_active=True
    )
    
    for comp in upcoming_competitions:
        days_until = (comp.event_date - today).days
        if days_until in [7, 3, 1]:  # Remind at 1 week, 3 days, and 1 day before
            council_members = User.objects.filter(is_active=True, role__isnull=False)
            
            for member in council_members:
                Notification.objects.create(
                    recipient=member,
                    notification_type='COMPETITION_DEADLINE',
                    title=f'⏰ Competition in {days_until} day{"s" if days_until > 1 else ""}: {comp.name}',
                    message=f'{comp.name} is coming up on {comp.event_date.strftime("%B %d")}!',
                    action_url='/competitions/',
                    send_email=days_until == 1  # Only send email for 1-day reminder
                )
