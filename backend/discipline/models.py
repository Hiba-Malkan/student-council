from django.db import models
from django.core.validators import RegexValidator
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