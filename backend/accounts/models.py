from django.contrib.auth.models import AbstractUser
from django.db import models

class Role(models.Model):
    """Role model with hierarchy and permissions"""
    ROLE_CATEGORIES = [
        ('C_SUITE', 'C-Suite'),
        ('CAPTAIN', 'Captain'),
        ('COORDINATOR', 'Coordinator'),
        ('CLASS_REP', 'Class Rep'),
        ('STUDENT', 'Student'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=20, choices=ROLE_CATEGORIES)
    description = models.TextField(blank=True)
    
    # Permissions
    can_edit_duty_roster = models.BooleanField(default=False)
    can_schedule_meetings = models.BooleanField(default=False)
    can_create_announcements = models.BooleanField(default=False)
    can_edit_announcements = models.BooleanField(default=False)
    can_manage_events = models.BooleanField(default=False)
    can_record_discipline = models.BooleanField(default=False)
    can_view_discipline = models.BooleanField(default=False)
    can_create_projects = models.BooleanField(default=False)
    can_approve_projects = models.BooleanField(default=False)
    
    # Hierarchy
    level = models.IntegerField(default=5)  # 1=highest (C-Suite), 5=lowest (Student)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['level', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class User(AbstractUser):
    """Custom user model with role-based access"""
    email = models.EmailField(unique=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, related_name='users')
    phone = models.CharField(max_length=20, blank=True)
    
    # Additional info
    grade = models.CharField(max_length=10, blank=True)
    section = models.CharField(max_length=10, blank=True)
    house = models.CharField(max_length=50, blank=True)  # House A/B/C/D
    
    # Phase for discipline tracking
    phase = models.CharField(max_length=20, blank=True)  # e.g., "Phase 1", "Phase 2"
    
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
        return self.role and self.role.category == 'C_SUITE'
    
    @property
    def is_captain(self):
        return self.role and self.role.category == 'CAPTAIN'
    
    @property
    def is_class_rep(self):
        return self.role and self.role.category == 'CLASS_REP'


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