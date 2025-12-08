from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role, UserSession


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'level', 'user_count']
    list_filter = ['category', 'level']
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'description', 'level')
        }),
        ('Permissions', {
            'fields': (
                'can_edit_duty_roster',
                'can_schedule_meetings',
                'can_create_announcements',
                'can_edit_announcements',
                'can_manage_events',
                'can_record_discipline',
                'can_view_discipline',
                'can_create_projects',
                'can_approve_projects',
            )
        }),
    )
    
    def user_count(self, obj):
        return obj.users.count()
    user_count.short_description = 'Number of Users'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'grade', 'house', 'is_staff']
    list_filter = ['role', 'grade', 'house', 'phase', 'is_staff', 'is_active', 'is_phase_head']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone', 'avatar', 'bio')}),
        ('Role & Academic Info', {'fields': ('role', 'grade', 'section', 'house', 'phase', 'is_phase_head')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'created_at', 'expires_at']
    list_filter = ['created_at', 'expires_at']
    search_fields = ['user__username', 'ip_address']
    readonly_fields = ['user', 'token', 'ip_address', 'user_agent', 'created_at', 'expires_at']