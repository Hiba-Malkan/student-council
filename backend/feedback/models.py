from django.db import models
from django.conf import settings


class Feedback(models.Model):
    """Model for storing user feedback and issue reports"""
    
    TYPE_CHOICES = [
        ('FEEDBACK', 'Feedback'),
        ('BUG', 'Bug Report'),
        ('FEATURE_REQUEST', 'Feature Request'),
        ('PERFORMANCE', 'Performance Issue'),
        ('OTHER', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    # User info
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='feedback_submitted'
    )
    name = models.CharField(max_length=200, blank=True, help_text="Name if not logged in")
    email = models.EmailField(blank=True, help_text="Email if not logged in")
    
    # Feedback details
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='FEEDBACK')
    category = models.CharField(
        max_length=100,
        blank=True,
        help_text="e.g., Announcements, Clubs, Competitions, etc."
    )
    subject = models.CharField(max_length=255)
    description = models.TextField()
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')
    
    # Attachments & metadata
    screenshot = models.ImageField(
        upload_to='feedback/screenshots/',
        blank=True,
        null=True,
        help_text="Screenshot or image related to the issue"
    )
    
    # Admin notes
    admin_notes = models.TextField(
        blank=True,
        help_text="Internal notes for admin/staff"
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='feedback_assigned'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Feedback'
        permissions = [
            ('can_manage_feedback', 'Can manage feedback and issues'),
        ]
    
    def __str__(self):
        return f"[{self.type}] {self.subject}"
    
    @property
    def submitter_name(self):
        """Get the name of who submitted this"""
        if self.submitted_by:
            return self.submitted_by.get_full_name() or self.submitted_by.username
        return self.name or "Anonymous"
