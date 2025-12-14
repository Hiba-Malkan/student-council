from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
import random
import string

class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    # Permissions
    is_normal_student = models.BooleanField(default=False)
    can_edit_duty_roster = models.BooleanField(default=False)
    can_schedule_meetings = models.BooleanField(default=False)
    can_create_announcements = models.BooleanField(default=False)
    can_edit_announcements = models.BooleanField(default=False)
    can_record_discipline = models.BooleanField(default=False)
    can_view_discipline = models.BooleanField(default=False)
    can_add_clubs = models.BooleanField(default=False)
    can_manage_competitions = models.BooleanField(default=False) 
    
    # Hierarchy    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class User(AbstractUser):
    """Custom user model with role-based access"""
    email = models.EmailField(unique=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, related_name='users')
    phone = models.CharField(max_length=20, blank=True)
    
    # Additional info
    grade = models.CharField(max_length=10, blank=True)
    section = models.CharField(max_length=10, blank=True)
    house = models.CharField(max_length=50, blank=True)  # House A/B/C/D
    
    is_phase_head = models.BooleanField(default=False)
    
    # Profile
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['username']
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} - {self.role}"
    
    @property
    def is_c_suite(self):
        """Check if user is in C-Suite (President, Vice President, Secretary, Treasurer)"""
        if not self.role:
            return False
        c_suite_roles = ['President', 'Vice President', 'Secretary', 'Treasurer']
        return self.role.name in c_suite_roles
    
    @property
    def is_captain(self):
        """Check if user is a Captain"""
        return self.role and 'Captain' in self.role.name
    
    @property
    def is_class_rep(self):
        """Check if user is a Class Representative"""
        return self.role and 'Class Rep' in self.role.name


class UserSession(models.Model):
    """Track user login sessions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    token = models.CharField(max_length=500)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        ordering = ['-created_at']
    

class PasswordResetOTP(models.Model):
    """Model to store OTPs for password reset"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_otps')
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'otp', 'is_used']),
        ]
    
    def __str__(self):
        return f"OTP for {self.user.username} - {'Used' if self.is_used else 'Active'}"
    
    @classmethod
    def generate_otp(cls):
        """Generate a 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=6))
    
    @classmethod
    def create_otp(cls, user, ip_address=None):
        """Create a new OTP for user"""
        otp_code = cls.generate_otp()
        expires_at = timezone.now() + timedelta(minutes=10)  # OTP valid for 10 minutes
        
        return cls.objects.create(
            user=user,
            otp=otp_code,
            expires_at=expires_at,
            ip_address=ip_address
        )
    
    def is_valid(self):
        """Check if OTP is still valid"""
        return not self.is_used and timezone.now() < self.expires_at
    
    def mark_as_used(self):
        """Mark OTP as used"""
        self.is_used = True
        self.save()

    def __str__(self):
        return f"{self.user.username} - {self.created_at}"


class ContactMessage(models.Model):
    """Model for users to contact administrators"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    ]
    
    name = models.CharField(max_length=200)
    email = models.EmailField()
    username = models.CharField(max_length=150, blank=True, help_text="If you have an account")
    subject = models.CharField(max_length=300)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Admin response
    admin_response = models.TextField(blank=True)
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_responses')
    responded_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"{self.subject} - {self.name} ({self.status})"

