# discipline/models.py
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from accounts.models import User


class DisciplineRecord(models.Model):
    """
    Model to track student discipline records
    """
    student_name = models.CharField(max_length=200)
    class_section = models.CharField(
        max_length=10,
        help_text="Format: e.g., 10A, 11B, 12C"
    )
    dno = models.CharField(
        max_length=9,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^D\d{4,8}$',
                message='Dno must be in format D followed by 4-8 digits (e.g., D1234 to D12345678)',
                code='invalid_dno'
            )
        ],
        help_text="Format: D followed by 4-8 digits (e.g., D1234 to D12345678)"
    )
    offense_count = models.PositiveIntegerField(
        default=1,
        help_text="Number of times offense occurred"
    )
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='discipline_records_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Discipline Record'
        verbose_name_plural = 'Discipline Records'

    def __str__(self):
        return f"{self.student_name} ({self.dno}) - {self.offense_count} offense(s)"


class OffenseLog(models.Model):
    """
    Individual offense log for each discipline record
    """
    record = models.ForeignKey(
        DisciplineRecord,
        on_delete=models.CASCADE,
        related_name='offense_logs'
    )
    
    CATEGORY_CHOICES = [
        ('UNIFORM', 'Uniform Violation'),
        ('LATE', 'Late Arrival / Submission'),
        ('BEHAVIOR', 'Misbehavior'),
        ('ACADEMIC', 'Academic Misconduct'),
        ('ABSENCE', 'Unauthorized Absence'),
        ('SUBSTANCES', 'Substances'),
        ('VPN', 'VPN Usage'),
        ('OTHER', 'Other'),
    ]
    
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='OTHER'
    )
    
    reason = models.TextField(
        blank=True,
        help_text="Detailed reason for this offense"
    )
    
    # Use created_at for offense date
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.record.dno} - {self.get_category_display()} on {self.created_at.date()}"


class DeletionLog(models.Model):
    """Audit trail of deleted discipline records and offense logs."""
    OBJECT_TYPE_CHOICES = [
        ('RECORD', 'Discipline Record'),
        ('OFFENSE', 'Offense Log'),
    ]
    
    object_type = models.CharField(
        max_length=10,
        choices=OBJECT_TYPE_CHOICES,
        default='OFFENSE'
    )
    
    # Snapshot of the deleted object
    dno = models.CharField(max_length=9, blank=True)
    student_name = models.CharField(max_length=200, blank=True)
    class_section = models.CharField(max_length=10, blank=True)
    offense_count = models.PositiveIntegerField(null=True, blank=True)
    category = models.CharField(
        max_length=20,
        choices=OffenseLog.CATEGORY_CHOICES,
        blank=True
    )
    reason = models.TextField(blank=True)
    
    # Who / when / why
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deletion_logs'
    )
    deleted_at = models.DateTimeField(default=timezone.now)
    note = models.TextField(
        blank=True,
        help_text="Optional context for this deletion"
    )
    
    class Meta:
        ordering = ['-deleted_at']
        indexes = [
            models.Index(fields=['deleted_at']),
            models.Index(fields=['dno']),
        ]
    
    def __str__(self):
        return f"{self.object_type} {self.dno or self.student_name} deleted on {self.deleted_at.date()}"