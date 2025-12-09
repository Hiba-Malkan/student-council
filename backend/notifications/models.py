from django.db import models
from accounts.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Notification(models.Model):
    """In-app and email notifications"""
    NOTIFICATION_TYPES = [
        ('MEETING_MORNING', 'Meeting Morning Reminder'),
        ('MEETING_10MIN', 'Meeting 10 Minute Reminder'),
        ('ANNOUNCEMENT', 'New Announcement'),
        ('DUTY_ASSIGNED', 'Duty Assigned'),
        ('DUTY_REMINDER', 'Duty Reminder'),
        ('EVENT_REGISTRATION', 'Event Registration'),
        ('GENERAL', 'General'),
    ]
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Link to related object
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Action link (URL to navigate to)
    action_url = models.CharField(max_length=500, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    is_snoozed = models.BooleanField(default=False)
    snoozed_until = models.DateTimeField(null=True, blank=True)
    
    # Email
    send_email = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['recipient', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.recipient.username} - {self.title}"


class EmailTemplate(models.Model):
    """Email templates for different notification types"""
    name = models.CharField(max_length=100, unique=True)
    subject = models.CharField(max_length=200)
    body_template = models.TextField()
    
    # Variables that can be used in template
    # e.g., {{user_name}}, {{meeting_title}}, {{date}}
    available_variables = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class NotificationPreference(models.Model):
    """User preferences for notifications"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Email preferences
    email_for_meetings = models.BooleanField(default=True)
    email_for_announcements = models.BooleanField(default=True)
    email_for_duties = models.BooleanField(default=True)
    email_for_discipline = models.BooleanField(default=True)
    email_for_projects = models.BooleanField(default=True)
    
    # In-app preferences
    in_app_for_meetings = models.BooleanField(default=True)
    in_app_for_announcements = models.BooleanField(default=True)
    in_app_for_duties = models.BooleanField(default=True)
    in_app_for_discipline = models.BooleanField(default=True)
    in_app_for_projects = models.BooleanField(default=True)
    
    # Digest preferences
    daily_digest = models.BooleanField(default=False)
    weekly_digest = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Notification preferences for {self.user.username}"


class NotificationBatch(models.Model):
    """Track batch notifications sent (e.g., daily discipline alerts)"""
    batch_type = models.CharField(max_length=50)
    sent_to_count = models.IntegerField(default=0)
    
    sent_at = models.DateTimeField(auto_now_add=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"{self.batch_type} - {self.sent_at}"