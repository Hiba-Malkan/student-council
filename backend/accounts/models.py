from django.contrib.auth.models import AbstractUser
from django.db import models

class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    # Permissions
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
    
    def __str__(self):
        return f"{self.user.username} - {self.created_at}"

