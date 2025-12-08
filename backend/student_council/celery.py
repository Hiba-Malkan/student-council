import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'student_council.settings')

app = Celery('student_council')

# Load config from Django settings with CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Periodic tasks schedule
app.conf.beat_schedule = {
    # Send morning meeting reminders at 7:00 AM
    'send-morning-meeting-reminders': {
        'task': 'notifications.tasks.send_morning_meeting_reminders',
        'schedule': crontab(hour=7, minute=0),
    },
    
    # Check for 10-minute meeting reminders every 5 minutes
    'send-10min-meeting-reminders': {
        'task': 'notifications.tasks.send_10min_meeting_reminders',
        'schedule': crontab(minute='*/5'),
    },
    
    # Send daily discipline report at 4:00 PM
    'send-daily-discipline-report': {
        'task': 'notifications.tasks.send_daily_discipline_report',
        'schedule': crontab(hour=16, minute=0),
    },
    
    # Check project deadlines daily at 8:00 AM
    'check-project-deadlines': {
        'task': 'notifications.tasks.check_project_deadlines',
        'schedule': crontab(hour=8, minute=0),
    },
    
    # Send duty reminders at 6:30 AM
    'send-duty-reminders': {
        'task': 'notifications.tasks.send_duty_reminders',
        'schedule': crontab(hour=6, minute=30),
    },
    
    # Check for defaulters daily at 3:00 PM
    'check-defaulters': {
        'task': 'notifications.tasks.check_defaulters',
        'schedule': crontab(hour=15, minute=0),
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')