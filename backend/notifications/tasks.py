from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count

from .models import Notification, NotificationPreference
from .utils import send_notification_email, send_daily_discipline_report
from accounts.models import User
from meetings.models import Meeting
from duty_roster.models import Duty
from discipline.models import DisciplineRecord
from competitions.models import Competition


@shared_task
def send_pending_email_notifications():
    """Send all pending email notifications"""
    # Get notifications that need email sending
    notifications = Notification.objects.filter(
        send_email=True,
        email_sent=False
    ).select_related('recipient')
    
    sent_count = 0
    
    for notification in notifications:
        # Check user preferences
        prefs = NotificationPreference.objects.filter(user=notification.recipient).first()
        
        if prefs:
            # Map notification types to preference fields
            type_to_pref = {
                'MEETING_CREATED': prefs.email_for_meetings,
                'MEETING_UPDATED': prefs.email_for_meetings,
                'MEETING_CANCELLED': prefs.email_for_meetings,
                'MEETING_REMINDER': prefs.email_for_meetings,
                'MEETING_MINUTES': prefs.email_for_meetings,
                'DUTY_ASSIGNED': prefs.email_for_duties,
                'DUTY_REMINDER': prefs.email_for_duties,
                'DUTY_COMPLETED': prefs.email_for_duties,
                'ANNOUNCEMENT_CREATED': prefs.email_for_announcements,
                'ANNOUNCEMENT_UPDATED': prefs.email_for_announcements,
                'COMPETITION_CREATED': prefs.email_for_competitions,
                'COMPETITION_DEADLINE': prefs.email_for_competitions,
                'COMPETITION_WINNER': prefs.email_for_competitions,
                'DISCIPLINE_OFFENSE': prefs.email_for_discipline,
                'DISCIPLINE_REPORT': prefs.email_for_discipline,
                'DISCIPLINE_RESOLVED': prefs.email_for_discipline,
            }
            
            # Skip if user disabled emails for this type
            if notification.notification_type in type_to_pref:
                if not type_to_pref[notification.notification_type]:
                    notification.email_sent = True
                    notification.save()
                    continue
        
        # Send the email
        try:
            send_notification_email(notification)
            sent_count += 1
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send email for notification {notification.id}: {e}", exc_info=True)
    
    return f"Sent {sent_count} email notifications"


@shared_task
def send_morning_meeting_reminders():
    """Send morning reminders for meetings today"""
    today = timezone.now().date()
    
    # Get meetings today
    meetings = Meeting.objects.filter(
        date=today,
        is_cancelled=False
    ).prefetch_related('attendees')
    
    notifications_created = 0
    
    for meeting in meetings:
        for attendee in meeting.attendees.all():
            # Check if notification already exists
            existing = Notification.objects.filter(
                recipient=attendee,
                notification_type='MEETING_REMINDER',
                created_at__date=today,
                message__contains=meeting.title
            ).exists()
            
            if not existing:
                Notification.objects.create(
                    recipient=attendee,
                    notification_type='MEETING_REMINDER',
                    title=f"Meeting Today: {meeting.title}",
                    message=f"Reminder: You have a meeting today at {meeting.time} - {meeting.title}",
                    action_url=f"/meetings/{meeting.id}",
                    send_email=True
                )
                notifications_created += 1
    
    return f"Created {notifications_created} meeting reminders"


@shared_task
def send_duty_reminders():
    """Send reminders for duties today"""
    today = timezone.now().date()
    
    duties = Duty.objects.filter(
        date=today
    ).select_related('assigned_to', 'duty_type')
    
    notifications_created = 0
    
    for duty in duties:
        # Check if notification already exists
        existing = Notification.objects.filter(
            recipient=duty.assigned_to,
            notification_type='DUTY_REMINDER',
            created_at__date=today,
            message__contains=duty.duty_type.name
        ).exists()
        
        if not existing:
            location = duty.location or (duty.duty_type.location if hasattr(duty.duty_type, 'location') else 'TBD')
            
            Notification.objects.create(
                recipient=duty.assigned_to,
                notification_type='DUTY_REMINDER',
                title=f"Duty Today: {duty.duty_type.name}",
                message=f"You have {duty.duty_type.name} duty today. Location: {location}",
                action_url=f"/duty-roster",
                send_email=True
            )
            notifications_created += 1
    
    return f"Created {notifications_created} duty reminders"


@shared_task
def send_discipline_reports():
    """Send daily discipline reports to phase heads for students with 3+ offenses"""
    # Get phase heads
    phase_heads = User.objects.filter(role__name__icontains='Phase Head')
    
    reports_sent = 0
    
    for phase_head in phase_heads:
        try:
            send_daily_discipline_report(phase_head)
            reports_sent += 1
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send discipline report to {phase_head.email}: {e}", exc_info=True)
    
    return f"Sent discipline reports to {reports_sent} phase heads"


@shared_task
def send_competition_deadline_reminders():
    """Send reminders for competitions with deadlines in 3 days"""
    three_days_from_now = timezone.now().date() + timedelta(days=3)
    
    competitions = Competition.objects.filter(
        deadline=three_days_from_now,
        is_active=True
    )
    
    notifications_created = 0
    
    # Send to all students
    students = User.objects.filter(role__name__icontains='Student')
    
    for competition in competitions:
        for student in students:
            # Check if notification already exists
            existing = Notification.objects.filter(
                recipient=student,
                notification_type='COMPETITION_DEADLINE',
                message__contains=competition.title
            ).exists()
            
            if not existing:
                Notification.objects.create(
                    recipient=student,
                    notification_type='COMPETITION_DEADLINE',
                    title=f"Competition Deadline Soon: {competition.title}",
                    message=f"The deadline for '{competition.title}' is in 3 days ({competition.deadline}). Don't miss out!",
                    action_url=f"/competitions/{competition.id}",
                    send_email=True
                )
                notifications_created += 1
    
    return f"Created {notifications_created} competition deadline reminders"


@shared_task
def send_daily_notifications():
    """Main task to send all daily notifications - Schedule this to run every morning"""
    results = []
    
    # Send morning meeting reminders
    results.append(send_morning_meeting_reminders())
    
    # Send duty reminders
    results.append(send_duty_reminders())
    
    # Send discipline reports
    results.append(send_discipline_reports())
    
    # Send competition deadline reminders
    results.append(send_competition_deadline_reminders())
    
    # Send all pending emails
    results.append(send_pending_email_notifications())
    
    return " | ".join(results)


@shared_task
def cleanup_old_notifications():
    """Delete read notifications older than 30 days"""
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    deleted_count = Notification.objects.filter(
        is_read=True,
        read_at__lt=thirty_days_ago
    ).delete()[0]
    
    return f"Deleted {deleted_count} old notifications"
