from django.db import models
from accounts.models import User, Role


class Announcement(models.Model):
    """Announcements and events"""
    ANNOUNCEMENT_TYPES = [
        ('GENERAL', 'General'),
        ('EVENT', 'Event'),
        ('URGENT', 'Urgent'),
        ('IH_SCHEDULE', 'Inter-House Schedule'),
        ('CULTURAL', 'Cultural Event'),
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    announcement_type = models.CharField(max_length=20, choices=ANNOUNCEMENT_TYPES, default='GENERAL')
    
    # Targeting
    target_roles = models.ManyToManyField(Role, related_name='announcements', blank=True)
    target_users = models.ManyToManyField(User, related_name='targeted_announcements', blank=True)
    target_houses = models.CharField(max_length=200, blank=True)  # Comma-separated: "A,B,C"
    target_grades = models.CharField(max_length=100, blank=True)  # Comma-separated: "9,10,11"
    is_public = models.BooleanField(default=False)  # Visible to all users
    
    # Event details (if announcement_type is EVENT)
    event_date = models.DateField(null=True, blank=True)
    event_time = models.TimeField(null=True, blank=True)
    event_location = models.CharField(max_length=200, blank=True)
    registration_required = models.BooleanField(default=False)
    registration_deadline = models.DateField(null=True, blank=True)
    
    # Attachments
    attachments = models.FileField(upload_to='announcements/', null=True, blank=True)
    
    # Publishing
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='announcements_created')
    is_published = models.BooleanField(default=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Email notification
    send_email = models.BooleanField(default=True)
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Priority
    is_pinned = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_pinned', '-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_announcement_type_display()})"


class EventParticipant(models.Model):
    """Track event participation"""
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_participations')
    
    # Registration
    registered_at = models.DateTimeField(auto_now_add=True)
    is_confirmed = models.BooleanField(default=False)
    
    # Assignment (by captains)
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='event_assignments'
    )
    role_in_event = models.CharField(max_length=100, blank=True)  # e.g., "Performer", "Organizer"
    
    # Status
    STATUS_CHOICES = [
        ('REGISTERED', 'Registered'),
        ('CONFIRMED', 'Confirmed'),
        ('ATTENDED', 'Attended'),
        ('ABSENT', 'Absent'),
        ('CANCELLED', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REGISTERED')
    
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['announcement', 'user']
        ordering = ['announcement', 'user']
    
    def __str__(self):
        return f"{self.user.username} - {self.announcement.title}"


class AnnouncementRead(models.Model):
    """Track which users have read which announcements"""
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='reads')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcements_read')
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['announcement', 'user']
        ordering = ['-read_at']
    
    def __str__(self):
        return f"{self.user.username} read {self.announcement.title}"