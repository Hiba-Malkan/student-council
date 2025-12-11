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
    # Send all daily notifications at 7:00 AM (meetings, duties, etc.)
    'send-daily-notifications': {
        'task': 'notifications.tasks.send_daily_notifications',
        'schedule': crontab(hour=7, minute=0),
    },
    
    # Send pending email notifications every 10 minutes
    'send-pending-emails': {
        'task': 'notifications.tasks.send_pending_email_notifications',
        'schedule': crontab(minute='*/10'),
    },
    
    # Send discipline reports at 4:00 PM
    'send-discipline-reports': {
        'task': 'notifications.tasks.send_discipline_reports',
        'schedule': crontab(hour=16, minute=0),
    },
    
    # Send competition deadline reminders at 8:00 AM
    'send-competition-deadline-reminders': {
        'task': 'notifications.tasks.send_competition_deadline_reminders',
        'schedule': crontab(hour=8, minute=0),
    },
    
    # Cleanup old notifications weekly on Sunday at 2:00 AM
    'cleanup-old-notifications': {
        'task': 'notifications.tasks.cleanup_old_notifications',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')