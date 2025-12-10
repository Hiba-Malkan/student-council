from django.db import models
from django.core.validators import RegexValidator
from accounts.models import User


class DisciplineRecord(models.Model):
    """
    Model to track student discipline records
    """
    student_name = models.CharField(max_length=200)
    class_section = models.CharField(
        max_length=50,
        help_text="e.g., '10-A', '12-B'"
    )
    dno = models.CharField(
        max_length=7,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^D\d{6}$',
                message='DNO must be in format Dxxxxxx (e.g., D123456)',
                code='invalid_dno'
            )
        ],
        help_text="Format: Dxxxxxx (e.g., D123456)"
    )
    offense_count = models.PositiveIntegerField(
        default=1,
        help_text="Number of times offense occurred"
    )
    
    # Tracking fields
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_discipline_records'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Discipline Record'
        verbose_name_plural = 'Discipline Records'

    def __str__(self):
        return f"{self.student_name} ({self.dno}) - {self.offense_count} offense(s)"