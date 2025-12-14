#!/usr/bin/env python
"""
Email Notification Diagnostic Script
Run this to check if your email notification system is properly configured.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'student_council.settings')
django.setup()

from django.conf import settings
from django.core.mail import send_mail
from notifications.models import Notification
import subprocess

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def check_redis():
    """Check if Redis is running"""
    print_header("Checking Redis")
    try:
        result = subprocess.run(['redis-cli', 'ping'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and 'PONG' in result.stdout:
            print("✅ Redis is running")
            return True
        else:
            print("❌ Redis is not responding")
            print("   Run: brew services start redis")
            return False
    except FileNotFoundError:
        print("❌ Redis is not installed")
        print("   Run: brew install redis")
        return False
    except Exception as e:
        print(f"❌ Error checking Redis: {e}")
        return False

def check_celery():
    """Check if Celery workers are running"""
    print_header("Checking Celery")
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        celery_processes = [line for line in result.stdout.split('\n') if 'celery' in line.lower() and 'worker' in line.lower()]
        
        if celery_processes:
            print(f"✅ Found {len(celery_processes)} Celery worker process(es)")
            return True
        else:
            print("❌ No Celery workers running")
            print("   Run: celery -A student_council worker --loglevel=info")
            return False
    except Exception as e:
        print(f"❌ Error checking Celery: {e}")
        return False

def check_celery_beat():
    """Check if Celery Beat is running"""
    print_header("Checking Celery Beat")
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        beat_processes = [line for line in result.stdout.split('\n') if 'celery' in line.lower() and 'beat' in line.lower()]
        
        if beat_processes:
            print(f"✅ Celery Beat is running")
            return True
        else:
            print("⚠️  Celery Beat is not running (scheduled tasks won't work)")
            print("   Run: celery -A student_council beat --loglevel=info")
            return False
    except Exception as e:
        print(f"❌ Error checking Celery Beat: {e}")
        return False

def check_email_settings():
    """Check email configuration"""
    print_header("Checking Email Configuration")
    
    issues = []
    
    print(f"Email Backend: {settings.EMAIL_BACKEND}")
    
    if 'console' in settings.EMAIL_BACKEND.lower():
        print("⚠️  Using console backend (emails print to terminal, not sent)")
    elif 'smtp' in settings.EMAIL_BACKEND.lower():
        print("✅ Using SMTP backend (will send real emails)")
        
        if not settings.EMAIL_HOST_USER:
            issues.append("EMAIL_HOST_USER not set")
            print("❌ EMAIL_HOST_USER is not configured")
        else:
            print(f"✅ Email User: {settings.EMAIL_HOST_USER}")
        
        if not settings.EMAIL_HOST_PASSWORD:
            issues.append("EMAIL_HOST_PASSWORD not set")
            print("❌ EMAIL_HOST_PASSWORD is not configured")
        else:
            print("✅ Email Password: ********** (set)")
        
        print(f"Email Host: {settings.EMAIL_HOST}")
        print(f"Email Port: {settings.EMAIL_PORT}")
        print(f"Use TLS: {settings.EMAIL_USE_TLS}")
        print(f"Default From: {settings.DEFAULT_FROM_EMAIL}")
    
    if issues:
        print("\n⚠️  Add these to your .env file:")
        print("   EMAIL_HOST_USER=your-email@gmail.com")
        print("   EMAIL_HOST_PASSWORD=your-app-password")
        print("   DEFAULT_FROM_EMAIL=your-email@gmail.com")
        print("\n   Get App Password: https://myaccount.google.com/apppasswords")
        return False
    
    return True

def check_pending_notifications():
    """Check for pending email notifications"""
    print_header("Checking Pending Notifications")
    
    pending = Notification.objects.filter(send_email=True, email_sent=False)
    count = pending.count()
    
    if count > 0:
        print(f"⚠️  {count} notification(s) waiting to be sent")
        print("\n   Recent pending notifications:")
        for notif in pending[:5]:
            print(f"   - {notif.title} (to: {notif.recipient.email})")
        
        if count > 5:
            print(f"   ... and {count - 5} more")
        
        print("\n   To send them manually:")
        print("   python manage.py shell")
        print("   >>> from notifications.tasks import send_pending_email_notifications")
        print("   >>> send_pending_email_notifications()")
    else:
        print("✅ No pending email notifications")
    
    return count

def test_email_sending():
    """Offer to send a test email"""
    print_header("Email Test")
    
    if not settings.EMAIL_HOST_USER:
        print("❌ Cannot test - email not configured")
        return False
    
    test_email = "hiba.malkan@gmail.com"
    response = input(f"Send test email to {test_email}? (y/n): ")
    
    if response.lower() == 'y':
        try:
            send_mail(
                'Student Council - Test Email',
                'This is a test email from the Student Council Management System. If you received this, emails are working! 🎉',
                settings.DEFAULT_FROM_EMAIL,
                [test_email],
                fail_silently=False,
            )
            print("✅ Test email sent successfully!")
            print(f"   Check your inbox: {test_email}")
            print("   (Also check spam folder if you don't see it)")
            return True
        except Exception as e:
            print(f"❌ Failed to send test email: {e}")
            print("\n   Common issues:")
            print("   - Wrong app password (must be 16-char app password from Google)")
            print("   - 2-Step Verification not enabled on Gmail")
            print("   - Wrong email address in EMAIL_HOST_USER")
            print("   - Gmail is blocking the login")
            return False
    else:
        print("Skipped test email")
        return None

def main():
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║   Email Notification System Diagnostic Tool              ║
    ║   Student Council Management System                      ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    results = {
        'redis': check_redis(),
        'celery': check_celery(),
        'celery_beat': check_celery_beat(),
        'email': check_email_settings(),
    }
    
    pending_count = check_pending_notifications()
    
    # Summary
    print_header("Summary")
    
    all_good = all(results.values())
    
    if all_good:
        print("✅ All systems are properly configured!")
        
        if pending_count > 0:
            print(f"\n⚠️  However, you have {pending_count} pending notifications")
            print("   Make sure Celery worker is processing them")
        
        # Offer to send test email
        test_email_sending()
    else:
        print("❌ Some issues need to be fixed:\n")
        
        if not results['redis']:
            print("   1. Install and start Redis")
            print("      brew install redis && brew services start redis\n")
        
        if not results['celery']:
            print("   2. Start Celery worker")
            print("      celery -A student_council worker --loglevel=info\n")
        
        if not results['celery_beat']:
            print("   3. Start Celery Beat (for scheduled tasks)")
            print("      celery -A student_council beat --loglevel=info\n")
        
        if not results['email']:
            print("   4. Configure email settings in .env file")
            print("      See EMAIL_TROUBLESHOOTING.md for detailed instructions\n")
    
    print("\n" + "="*60)
    print("For detailed help, see: EMAIL_TROUBLESHOOTING.md")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
