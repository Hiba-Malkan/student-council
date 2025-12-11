from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from notifications.models import Notification
from notifications.utils import send_notification_email
from accounts.models import User


class Command(BaseCommand):
    help = 'Send a test email notification'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to send to',
            default='hiba.malkan@gmail.com'
        )

    def handle(self, *args, **options):
        email = options['email']
        
        self.stdout.write(self.style.WARNING(f'Attempting to send test email to {email}...'))
        
        # Try to find user by email, or use first user
        user = User.objects.filter(email=email).first()
        if not user:
            user = User.objects.first()
            self.stdout.write(self.style.WARNING(f'User with email {email} not found, using {user.email} instead'))
        
        # Create notification
        notification = Notification.objects.create(
            recipient=user,
            notification_type='MEETING_REMINDER',
            title='🎉 Test Email from Student Council App',
            message=f'''Hello {user.get_full_name() or user.username}!

This is a test email from the Student Council Management System.

If you're receiving this, it means the notification system is working perfectly! ✅

Features:
• Automated meeting reminders
• Duty roster notifications
• Discipline reports for phase heads
• Competition deadline alerts
• Announcement broadcasts

Have a great day!

- Student Council Team''',
            action_url='/dashboard/',
            send_email=True
        )
        
        try:
            # Send email
            send_notification_email(notification)
            
            if notification.email_sent:
                self.stdout.write(self.style.SUCCESS(f'✅ Email sent successfully to {user.email}!'))
                self.stdout.write(f'Notification ID: {notification.id}')
                self.stdout.write(f'Sent at: {notification.email_sent_at}')
            else:
                self.stdout.write(self.style.ERROR('❌ Email sending failed'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
            
            # Show troubleshooting tips
            self.stdout.write(self.style.WARNING('\n📝 Troubleshooting tips:'))
            self.stdout.write('1. Make sure EMAIL_HOST_USER and EMAIL_HOST_PASSWORD are set')
            self.stdout.write('2. For Gmail, use an App Password (not your regular password)')
            self.stdout.write('3. Check if EMAIL_BACKEND is set to smtp.EmailBackend')
            self.stdout.write('4. Run: pip install --upgrade certifi (for SSL issues)')
