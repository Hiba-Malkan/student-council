from django.db import models
from django.conf import settings


class Club(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('under_review', 'Under Review'),
        ('inactive', 'Inactive'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    logo = models.ImageField(upload_to='club_logos/', null=True, blank=True)
    
    # Membership & History
    member_count = models.PositiveIntegerField(default=0)
    established_year = models.PositiveIntegerField()
    established_by = models.CharField(max_length=500, help_text="Comma-separated names of founders")
    
    # Faculty
    tutors = models.CharField(max_length=500, help_text="Comma-separated names of faculty tutors")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='under_review')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='clubs_created'
    )
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    @property
    def founders_list(self):
        """Return list of founders"""
        return [name.strip() for name in self.established_by.split(',') if name.strip()]
    
    @property
    def tutors_list(self):
        """Return list of tutors"""
        return [name.strip() for name in self.tutors.split(',') if name.strip()]


class ClubSignup(models.Model):
    """Track public signups for clubs"""
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='signups')
    student_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('club', 'email')  # Prevent duplicate signups from same email
    
    def __str__(self):
        return f"{self.student_name} - {self.club.name}"