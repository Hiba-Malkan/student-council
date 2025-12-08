from celery import shared_task
from django.core.mail import send_mail, send_mass_mail
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta, date
from django.db.models import Count, Q

from .models import Notification, NotificationBatch
from accounts.models import User
from meetings.models import Meeting
from duty_roster.models import Duty
from discipline.models import DisciplineOffence, DefaulterReport
from projects.models import Project


@shared_task
def send_email_notification(notification_id):
    """Send email for a specific notification"""
    try:
        notification = Notification.objects.get(id=notification_id)
        
        if notification.email_sent:
            return f"Email already sent for notification {notification_id}"
        
        # Check user preferences
        if hasattr(notification.recipient, 'notification_preferences'):
            prefs = notification.recipient.notification_preferences
            
            # Check if user wants emails for this type
            type_mapping = {
                'MEETING_MORNING': prefs.email_for_meetings,
                'MEETING_10MIN': prefs.email_for_meetings,
                'ANNOUNCEMENT': prefs.email_for_announcements,
                'DUTY_ASSIGNED': prefs.email_for_duties,
                'DUTY_REMINDER': prefs.email_for_duties,
                'DISCIPLINE_ALERT': prefs.email_for_discipline,
                'PROJECT_DEADLINE': prefs.email_for_projects,
                'PROJECT_APPROVAL': prefs.email_for_projects,
            }
            
            if not type_mapping.get(notification.notification_type, True):
                return f"User disabled emails for {notification.notification_type}"
        
        # Send email
        send_mail(
            subject=notification.title,
            message=notification.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.recipient.email],
            fail_silently=False,
        )
        
        # Mark as sent
        notification.email_sent = True
        notification.email_sent_at = timezone.now()
        notification.save()
        
        return f"Email sent successfully to {notification.recipient.email}"
    
    except Notification.DoesNotExist:
        return f"Notification {notification_id} not found"
    except Exception as e:
        return f"Error sending email: {str(e)}"


@shared_task
def send_morning_meeting_reminders():
    """Send morning reminders for meetings today"""
    today = timezone.now().date()
    
    # Get meetings today that haven't sent morning reminder
    meetings = Meeting.objects.filter(
        date=today,
        is_cancelled=False,
        morning_reminder_sent=False
    )
    
    notifications_created = 0
    
    for meeting in meetings:
        # Get all attendees
        attendees = list(meeting.attendees.all())
        
        # Get users from attendee roles
        role_users = User.objects.filter(role__in=meeting.attendee_roles.all())
        attendees.extend(role_users)
        
        # Remove duplicates
        attendees = list(set(attendees))
        
        for user in attendees:
            notification = Notification.objects.create(
                recipient=user,
                notification_type='MEETING_MORNING',
                title=f"Meeting Today: {meeting.title}",
                message=f"Reminder: You have a meeting today at {meeting.start_time} - {meeting.title}\nLocation: {meeting.location}",
                action_url=f"/meetings/{meeting.id}",
                send_email=True
            )
            
            # Queue email
            send_email_notification.delay(notification.id)
            notifications_created += 1
        
        # Mark reminder as sent
        meeting.morning_reminder_sent = True
        meeting.save()
    
    return f"Morning reminders sent for {meetings.count()} meetings to {notifications_created} users"


@shared_task
def send_10min_meeting_reminders():
    """Send 10-minute reminders for upcoming meetings"""
    now = timezone.now()
    ten_min_later = now + timedelta(minutes=10)
    fifteen_min_later = now + timedelta(minutes=15)
    
    # Get meetings starting in next 10-15 minutes that haven't sent 10-min reminder
    meetings = Meeting.objects.filter(
        date=now.date(),
        start_time__gte=ten_min_later.time(),
        start_time__lte=fifteen_min_later.time(),
        is_cancelled=False,
        ten_min_reminder_sent=False
    )
    
    notifications_created = 0
    
    for meeting in meetings:
        attendees = list(meeting.attendees.all())
        role_users = User.objects.filter(role__in=meeting.attendee_roles.all())
        attendees.extend(role_users)
        attendees = list(set(attendees))
        
        for user in attendees:
            notification = Notification.objects.create(
                recipient=user,
                notification_type='MEETING_10MIN',
                title=f"Meeting in 10 Minutes: {meeting.title}",
                message=f"Your meeting '{meeting.title}' starts in 10 minutes!\nLocation: {meeting.location}",
                action_url=f"/meetings/{meeting.id}",
                send_email=True
            )
            
            send_email_notification.delay(notification.id)
            notifications_created += 1
        
        meeting.ten_min_reminder_sent = True
        meeting.save()
    
    return f"10-minute reminders sent for {meetings.count()} meetings to {notifications_created} users"


@shared_task
def send_duty_reminders():
    """Send reminders for duties today"""
    today = timezone.now().date()
    
    duties = Duty.objects.filter(
        date=today,
        is_completed=False
    )
    
    notifications_created = 0
    
    for duty in duties:
        notification = Notification.objects.create(
            recipient=duty.assigned_to,
            notification_type='DUTY_REMINDER',
            title=f"Duty Today: {duty.duty_type.name}",
            message=f"Reminder: You have {duty.duty_type.name} duty today from {duty.start_time} to {duty.end_time}\nLocation: {duty.location or duty.duty_type.location}",
            action_url=f"/duties/{duty.id}",
            send_email=True
        )
        
        send_email_notification.delay(notification.id)
        notifications_created += 1
    
    return f"Duty reminders sent to {notifications_created} users"


@shared_task
def send_daily_discipline_report():
    """Send daily discipline report to phase heads"""
    today = timezone.now().date()
    
    # Get today's offences grouped by phase
    offences = DisciplineOffence.objects.filter(date=today)
    
    if not offences.exists():
        return "No offences recorded today"
    
    # Get phase heads
    phase_heads = User.objects.filter(is_phase_head=True)
    
    notifications_created = 0
    
    for phase_head in phase_heads:
        # Get offences for this phase head's phase
        phase_offences = offences.filter(student__phase=phase_head.phase)
        
        if phase_offences.exists():
            offence_list = "\n".join([
                f"- {offence.student.get_full_name()}: {offence.offence_type.name}"
                for offence in phase_offences
            ])
            
            notification = Notification.objects.create(
                recipient=phase_head,
                notification_type='DISCIPLINE_ALERT',
                title=f"Daily Discipline Report - {phase_head.phase}",
                message=f"Discipline offences recorded today for {phase_head.phase}:\n\n{offence_list}\n\nTotal: {phase_offences.count()} offences",
                action_url="/discipline/offences",
                send_email=True
            )
            
            send_email_notification.delay(notification.id)
            notifications_created += 1
    
    # Create batch record
    NotificationBatch.objects.create(
        batch_type='DAILY_DISCIPLINE_REPORT',
        sent_to_count=notifications_created,
        metadata={'offences_count': offences.count(), 'date': str(today)}
    )
    
    return f"Daily discipline report sent to {notifications_created} phase heads"


@shared_task
def check_defaulters():
    """Check for students with 3+ offences and create defaulter reports"""
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    
    # Get students with 3+ offences in last 30 days grouped by phase
    defaulters_by_phase = {}
    
    offences = DisciplineOffence.objects.filter(
        date__gte=thirty_days_ago,
        date__lte=today
    ).values('student', 'student__phase').annotate(
        offence_count=Count('id')
    ).filter(offence_count__gte=3)
    
    for item in offences:
        phase = item['student__phase']
        if phase not in defaulters_by_phase:
            defaulters_by_phase[phase] = []
        defaulters_by_phase[phase].append(item['student'])
    
    reports_created = 0
    
    for phase, student_ids in defaulters_by_phase.items():
        # Create or update defaulter report
        report, created = DefaulterReport.objects.get_or_create(
            date=today,
            phase=phase
        )
        
        # Add defaulters
        students = User.objects.filter(id__in=student_ids)
        report.defaulters.set(students)
        
        if created:
            reports_created += 1
            
            # Notify phase heads
            phase_heads = User.objects.filter(is_phase_head=True, phase=phase)
            
            for phase_head in phase_heads:
                defaulter_names = ", ".join([s.get_full_name() for s in students])
                
                notification = Notification.objects.create(
                    recipient=phase_head,
                    notification_type='DISCIPLINE_ALERT',
                    title=f"Defaulter Alert - {phase}",
                    message=f"The following students have 3 or more offences in the last 30 days:\n\n{defaulter_names}\n\nPlease review and take appropriate action.",
                    action_url=f"/discipline/defaulter-reports/{report.id}",
                    send_email=True
                )
                
                send_email_notification.delay(notification.id)
    
    return f"Created {reports_created} defaulter reports for {len(defaulters_by_phase)} phases"


@shared_task
def check_project_deadlines():
    """Check for upcoming project deadlines and send reminders"""
    today = timezone.now().date()
    seven_days_later = today + timedelta(days=7)
    
    # Get projects with deadlines in next 7 days
    projects = Project.objects.filter(
        deadline__gte=today,
        deadline__lte=seven_days_later,
        status__in=['APPROVED', 'IN_PROGRESS']
    )
    
    notifications_created = 0
    
    for project in projects:
        days_left = (project.deadline - today).days
        
        # Get all assigned users
        assigned_users = project.assigned_to.all()
        
        for user in assigned_users:
            notification = Notification.objects.create(
                recipient=user,
                notification_type='PROJECT_DEADLINE',
                title=f"Project Deadline Approaching: {project.title}",
                message=f"The project '{project.title}' is due in {days_left} days (Deadline: {project.deadline}).\n\nPlease ensure all tasks are completed on time.",
                action_url=f"/projects/{project.id}",
                send_email=True
            )
            
            send_email_notification.delay(notification.id)
            notifications_created += 1
        
        # Also notify the proposer
        if project.proposed_by and project.proposed_by not in assigned_users:
            notification = Notification.objects.create(
                recipient=project.proposed_by,
                notification_type='PROJECT_DEADLINE',
                title=f"Project Deadline Approaching: {project.title}",
                message=f"Your project '{project.title}' is due in {days_left} days (Deadline: {project.deadline}).",
                action_url=f"/projects/{project.id}",
                send_email=True
            )
            
            send_email_notification.delay(notification.id)
            notifications_created += 1
    
    return f"Deadline reminders sent for {projects.count()} projects to {notifications_created} users"


@shared_task
def send_announcement_notifications(announcement_id):
    """Send notifications for a new announcement"""
    from announcements.models import Announcement
    
    try:
        announcement = Announcement.objects.get(id=announcement_id)
        
        if not announcement.send_email or announcement.email_sent:
            return "Email notifications not required or already sent"
        
        # Get target users
        target_users = set()
        
        # Add directly targeted users
        target_users.update(announcement.target_users.all())
        
        # Add users from targeted roles
        if announcement.target_roles.exists():
            role_users = User.objects.filter(role__in=announcement.target_roles.all())
            target_users.update(role_users)
        
        # Add users from targeted houses
        if announcement.target_houses:
            houses = [h.strip() for h in announcement.target_houses.split(',')]
            house_users = User.objects.filter(house__in=houses)
            target_users.update(house_users)
        
        # Add users from targeted grades
        if announcement.target_grades:
            grades = [g.strip() for g in announcement.target_grades.split(',')]
            grade_users = User.objects.filter(grade__in=grades)
            target_users.update(grade_users)
        
        # If public, send to all active users
        if announcement.is_public:
            target_users.update(User.objects.filter(is_active=True))
        
        notifications_created = 0
        
        for user in target_users:
            notification = Notification.objects.create(
                recipient=user,
                notification_type='ANNOUNCEMENT',
                title=f"New Announcement: {announcement.title}",
                message=announcement.content[:500],  # Truncate if too long
                action_url=f"/announcements/{announcement.id}",
                send_email=True
            )
            
            send_email_notification.delay(notification.id)
            notifications_created += 1
        
        # Mark announcement as emailed
        announcement.email_sent = True
        announcement.email_sent_at = timezone.now()
        announcement.save()
        
        return f"Announcement notifications sent to {notifications_created} users"
    
    except Announcement.DoesNotExist:
        return f"Announcement {announcement_id} not found"