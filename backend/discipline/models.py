from django.db import models
from accounts.models import User


class OffenceType(models.Model):
    """Types of disciplinary offences"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    severity = models.IntegerField(default=1)  # 1=Minor, 2=Moderate, 3=Major
    points = models.IntegerField(default=1)  # Points for tracking threshold
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-severity', 'name']
    
    def __str__(self):
        return f"{self.name} (Severity: {self.severity})"


class DisciplineOffence(models.Model):
    """Record of disciplinary offence"""
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discipline_offences')
    offence_type = models.ForeignKey(OffenceType, on_delete=models.CASCADE, related_name='offences')
    
    date = models.DateField()
    time = models.TimeField(auto_now_add=True)
    location = models.CharField(max_length=200, blank=True)
    
    description = models.TextField(blank=True)
    photo = models.ImageField(upload_to='discipline/offences/', null=True, blank=True)
    
    # Recorded by
    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='offences_recorded'
    )
    
    # Status
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('REVIEWED', 'Reviewed'),
        ('RESOLVED', 'Resolved'),
        ('ESCALATED', 'Escalated'),
        ('DISMISSED', 'Dismissed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Phase head review
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='offences_reviewed'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    # Action taken
    action_taken = models.TextField(blank=True)
    parent_notified = models.BooleanField(default=False)
    parent_notification_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-time']
    
    def __str__(self):
        return f"{self.student.username} - {self.offence_type.name} on {self.date}"


class DefaulterReport(models.Model):
    """Daily defaulter report for phase heads"""
    date = models.DateField()
    phase = models.CharField(max_length=20)
    
    # Students who reached threshold (e.g., 3 offences)
    defaulters = models.ManyToManyField(User, related_name='defaulter_reports')
    
    # Report status
    generated_at = models.DateTimeField(auto_now_add=True)
    sent_to_phase_heads = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-date']
        unique_together = ['date', 'phase']
    
    def __str__(self):
        return f"Defaulter Report - {self.phase} on {self.date}"


class DisciplineAction(models.Model):
    """Actions taken for discipline cases"""
    ACTION_TYPES = [
        ('WARNING', 'Warning'),
        ('DETENTION', 'Detention'),
        ('SUSPENSION', 'Suspension'),
        ('PARENT_MEETING', 'Parent Meeting'),
        ('COMMUNITY_SERVICE', 'Community Service'),
        ('OTHER', 'Other'),
    ]
    
    offence = models.ForeignKey(DisciplineOffence, on_delete=models.CASCADE, related_name='actions')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    
    description = models.TextField()
    date_assigned = models.DateField()
    date_completed = models.DateField(null=True, blank=True)
    
    is_completed = models.BooleanField(default=False)
    
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='discipline_actions_assigned'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_assigned']
    
    def __str__(self):
        return f"{self.get_action_type_display()} for {self.offence.student.username}"