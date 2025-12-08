from django.db import models
from accounts.models import User, Role


class Meeting(models.Model):
    """Meeting scheduling and management"""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    date = models.DateField()
    
    location = models.CharField(max_length=200)
    meeting_link = models.URLField(blank=True)  # For virtual meetings
    
    # Attendees
    attendees = models.ManyToManyField(User, related_name='meetings_attending', blank=True)
    attendee_roles = models.ManyToManyField(Role, related_name='meetings', blank=True)
    
    # Organization
    organized_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='meetings_organized'
    )
    
    # Agenda and notes
    agenda = models.TextField(blank=True)
    
    # Status
    is_cancelled = models.BooleanField(default=False)
    cancellation_reason = models.TextField(blank=True)
    
    # Reminders sent
    morning_reminder_sent = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['date']
    
    def __str__(self):
        return f"{self.title} - {self.date}"


class MinutesOfMeeting(models.Model):
    """Minutes of Meeting (MoM)"""
    meeting = models.OneToOneField(Meeting, on_delete=models.CASCADE, related_name='mom')
    
    content = models.TextField()
    
    # Attachments
    document = models.FileField(upload_to='meetings/mom/', null=True, blank=True)
    
    # Present and absent
    present = models.ManyToManyField(User, related_name='meetings_present', blank=True)
    absent = models.ManyToManyField(User, related_name='meetings_absent', blank=True)
    
    # Action items
    action_items = models.TextField(blank=True)
    
    # Upload info
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='moms_uploaded'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Email status
    emailed_to_phase_heads = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Minutes of Meetings'
    
    def __str__(self):
        return f"MoM for {self.meeting.title}"


class MeetingAttendance(models.Model):
    """Track meeting attendance"""
    ATTENDANCE_STATUS = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LATE', 'Late'),
        ('EXCUSED', 'Excused'),
    ]
    
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='attendance')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meeting_attendance')
    
    status = models.CharField(max_length=20, choices=ATTENDANCE_STATUS, default='ABSENT')
    notes = models.TextField(blank=True)
    
    marked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='attendance_marked'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['meeting', 'user']
        ordering = ['meeting', 'user']
    
    def __str__(self):
        return f"{self.user.username} - {self.meeting.title}: {self.status}"