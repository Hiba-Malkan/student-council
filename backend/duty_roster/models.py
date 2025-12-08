from django.db import models
from accounts.models import User

class DutyType(models.Model):
    """Types of duties (e.g., Morning Duty, Lunch Duty, Library Duty)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    color = models.CharField(max_length=7, default='#3B82F6')  # Hex color code
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Duty(models.Model):
    """Individual duty assignment"""
    # Keep BOTH fields during transition
    duty_type = models.ForeignKey(
        DutyType, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,  # Make optional for new free-text entries
        related_name='duties'
    )
    
    duty_type_name = models.CharField(max_length=100)  # Free text field for duty type
    
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='duties')
    date = models.DateField()
    
    location = models.CharField(max_length=200, blank=True)
    subsidiary_area = models.CharField(max_length=200, blank=True)  # New field for floor/subsidiary area
    instructions = models.TextField(blank=True)
    
    # Status tracking
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)  # Notes after completion
    
    # Assignment details
    assigned_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='duties_assigned'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['date']
        verbose_name_plural = 'Duties'
        unique_together = ['assigned_to', 'date', 'duty_type_name']  # Updated constraint
    
    def __str__(self):
        return f"{self.duty_type_name} - {self.assigned_to.username} on {self.date}"
    
    def save(self, *args, **kwargs):
        # If we have a duty_type ForeignKey but no duty_type_name, populate it
        if self.duty_type and not self.duty_type_name:
            self.duty_type_name = self.duty_type.name
        super().save(*args, **kwargs)
    
    @property
    def display_duty_type(self):
        """Helper property to get the duty type name"""
        return self.duty_type_name or (self.duty_type.name if self.duty_type else '')
