from django.db import models
from django.conf import settings


class Competition(models.Model):
    """Model for storing competition information"""
    
    name = models.CharField(max_length=200)
    hosted_by = models.TextField(help_text="Comma-separated list of hosts")
    participants = models.TextField(blank=True, help_text="Comma-separated list of participants")
    participant_count = models.PositiveIntegerField(default=0)
    event_link = models.URLField(blank=True, null=True)
    brochure = models.FileField(upload_to='competitions/brochures/', blank=True, null=True)
    additional_info = models.TextField(blank=True)
    
    # Event details (optional, for modal display)
    event_date = models.DateField(blank=True, null=True)
    event_time = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=200, blank=True)
    team_size = models.CharField(max_length=50, blank=True, help_text="e.g., '2-4 members'")
    description = models.TextField(blank=True)
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='competitions_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return self.name
    
    @property
    def hosts_list(self):
        """Return list of hosts"""
        return [host.strip() for host in self.hosted_by.split(',') if host.strip()]
    
    @property
    def participants_list(self):
        """Return list of participants"""
        if not self.participants:
            return []
        return [p.strip() for p in self.participants.split(',') if p.strip()]


class CompetitionSignup(models.Model):
    """Track public signups for competitions"""
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='signups')
    student_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    team_name = models.CharField(max_length=200, blank=True)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('competition', 'email')  # Prevent duplicate signups from same email
    
    def __str__(self):
        return f"{self.student_name} - {self.competition.name}"