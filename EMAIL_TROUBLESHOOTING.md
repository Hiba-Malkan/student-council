# Email Notifications Troubleshooting Guide

## Issue: Email Notifications Not Sending

Your notification system is properly set up in the code, but emails require specific configuration and services to be running. Here's how to fix it:

## Root Causes (Most Likely)

1. **Missing Email Credentials** - No EMAIL_HOST_USER/EMAIL_HOST_PASSWORD in .env
2. **Celery Not Running** - Background tasks that send emails aren't executing
3. **Redis Not Running** - Celery broker isn't available
4. **Gmail App Password Not Set** - Gmail blocks "less secure" logins

---

## Quick Diagnosis

Run these commands to check what's working:

```bash
cd /Users/hiba/student-council/backend

# Check if Redis is running
redis-cli ping
# Should return: PONG

# Check if Celery workers are running
ps aux | grep celery

# Check if email settings are configured
python manage.py shell
>>> from django.conf import settings
>>> print(f"Email Host: {settings.EMAIL_HOST}")
>>> print(f"Email User: {settings.EMAIL_HOST_USER}")
>>> print(f"Email Password: {'SET' if settings.EMAIL_HOST_PASSWORD else 'NOT SET'}")
>>> exit()
```

---

## Solution 1: Configure Email Settings

### Step 1: Get Gmail App Password

If using Gmail (recommended for development):

1. Go to your Google Account: https://myaccount.google.com/
2. Click **Security** in the left menu
3. Enable **2-Step Verification** (if not already enabled)
4. Search for "App passwords" or go to: https://myaccount.google.com/apppasswords
5. Create a new app password:
   - App: "Mail"
   - Device: "Mac" or "Other (Custom name)" → "Student Council App"
6. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

### Step 2: Update .env File

Add to `/Users/hiba/student-council/backend/.env`:

```bash
# Email Configuration (Gmail)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password-here
DEFAULT_FROM_EMAIL=your-email@gmail.com
SITE_URL=http://localhost:8000
```

**Important:** Use the App Password, NOT your regular Gmail password!

### Alternative: Use Console Backend (Development Only)

To see emails in the terminal instead of sending real emails:

In `settings.py`, change:
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Print to console
```

---

## Solution 2: Install and Start Redis

Celery needs Redis as a message broker.

### Install Redis (macOS)

```bash
# Install via Homebrew
brew install redis

# Start Redis
brew services start redis

# Verify it's running
redis-cli ping
# Should return: PONG
```

### Alternative: Use RabbitMQ

If you prefer RabbitMQ over Redis:

```bash
brew install rabbitmq
brew services start rabbitmq
```

Update `.env`:
```bash
CELERY_BROKER_URL=amqp://localhost
CELERY_RESULT_BACKEND=rpc://
```

---

## Solution 3: Start Celery Workers

Celery workers process background tasks (including sending emails).

### Terminal 1: Start Celery Worker

```bash
cd /Users/hiba/student-council/backend
python manage.py runserver  # Your Django server
```

### Terminal 2: Start Celery Worker

```bash
cd /Users/hiba/student-council/backend
celery -A student_council worker --loglevel=info
```

### Terminal 3: Start Celery Beat (Scheduled Tasks)

```bash
cd /Users/hiba/student-council/backend
celery -A student_council beat --loglevel=info
```

**Note:** Celery Beat sends scheduled notifications (morning reminders, etc.)

---

## Solution 4: Test Email Sending

After configuration, test if emails work:

```bash
cd /Users/hiba/student-council/backend
python manage.py shell
```

```python
from django.core.mail import send_mail
from django.conf import settings

# Test email
send_mail(
    'Test Email',
    'This is a test email from Student Council App.',
    settings.DEFAULT_FROM_EMAIL,
    ['your-email@gmail.com'],
    fail_silently=False,
)
# If no error, check your inbox!
```

---

## Solution 5: Manually Trigger Email Notifications

Force send pending notifications:

```bash
cd /Users/hiba/student-council/backend
python manage.py shell
```

```python
from notifications.tasks import send_pending_email_notifications

# Manually trigger the task
result = send_pending_email_notifications()
print(result)
```

---

## Complete Setup Script

Save this as `start_services.sh`:

```bash
#!/bin/bash

# Start all services for Student Council App

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "Starting Redis..."
    brew services start redis
    sleep 2
fi

# Start Django (Terminal 1)
echo "Starting Django server..."
osascript -e 'tell app "Terminal" to do script "cd /Users/hiba/student-council/backend && python manage.py runserver"'

# Start Celery Worker (Terminal 2)
echo "Starting Celery worker..."
osascript -e 'tell app "Terminal" to do script "cd /Users/hiba/student-council/backend && celery -A student_council worker --loglevel=info"'

# Start Celery Beat (Terminal 3)
echo "Starting Celery beat..."
osascript -e 'tell app "Terminal" to do script "cd /Users/hiba/student-council/backend && celery -A student_council beat --loglevel=info"'

echo "All services started!"
```

Make it executable:
```bash
chmod +x start_services.sh
./start_services.sh
```

---

## Notification Schedule

Your notifications are scheduled to send at:

- **7:00 AM** - Daily notifications (meetings, duties)
- **Every 10 minutes** - Pending email notifications
- **4:00 PM** - Discipline reports
- **8:00 AM** - Competition deadline reminders
- **2:00 AM Sunday** - Cleanup old notifications

---

## Verification Checklist

✅ **Redis is running** - `redis-cli ping` returns PONG
✅ **Email credentials set** - Check .env file
✅ **Celery worker running** - See worker logs in terminal
✅ **Celery beat running** - See beat logs in terminal
✅ **Django server running** - http://localhost:8000 accessible
✅ **Test email sent successfully** - Check inbox/spam

---

## Common Issues

### Issue: "Connection refused" for Redis
**Solution:** Start Redis: `brew services start redis`

### Issue: "SMTP Authentication Error"
**Solution:** Use Gmail App Password, not regular password

### Issue: Emails in spam folder
**Solution:** Add sender to contacts, mark as "Not spam"

### Issue: Celery worker not picking up tasks
**Solution:** Restart worker after code changes

### Issue: Tasks not scheduled
**Solution:** Make sure Celery Beat is running

---

## Production Deployment

For production, use:

1. **Supervisor** or **systemd** to keep Celery running
2. **Real email service** (SendGrid, AWS SES, Mailgun)
3. **Environment variables** for all secrets
4. **HTTPS** for SITE_URL

---

## Quick Commands Reference

```bash
# Start Redis
brew services start redis

# Stop Redis
brew services stop redis

# Start Celery Worker
celery -A student_council worker -l info

# Start Celery Beat
celery -A student_council beat -l info

# Check Celery tasks
celery -A student_council inspect active

# Purge all tasks
celery -A student_council purge

# Test email in Django shell
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Body', 'from@email.com', ['to@email.com'])
```

---

## Need Help?

If emails still don't work after following this guide:

1. Check Celery worker logs for errors
2. Check Django server logs
3. Verify email credentials are correct
4. Try console backend to see if notifications are being created
5. Check spam folder
6. Verify user has email address set in database
