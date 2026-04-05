from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class GatePass(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
    ]
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gatepass_requests')
    dno = models.CharField(max_length=50, verbose_name='D.No / Room Number', default='')
    name = models.CharField(max_length=255, default='')
    student_class = models.CharField(max_length=50, verbose_name="Class", default='')
    student_section = models.CharField(max_length=50, verbose_name="Section", default='')
    parent_email = models.EmailField(default='')
    ct_email = models.EmailField(blank=True, null=True, verbose_name="Class Teacher Email (Optional)")
    requested_date = models.DateField(default=timezone.now)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Approval info
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='gatepass_approvals')
    approval_note = models.TextField(blank=True)
    approval_timestamp = models.DateTimeField(null=True, blank=True)
    
    # Dates
    requested_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"{self.student.username} - {self.status.upper()}"
