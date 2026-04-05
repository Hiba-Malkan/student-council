from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import Role, User, UserSession, ContactMessage

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'user_count', 'created_at']
    list_filter = ['can_edit_duty_roster', 'can_schedule_meetings', 'can_create_announcements']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name',)
        }),
        ('Permissions', {
            'fields': (
                'is_normal_student',
                'can_edit_duty_roster',
                'can_schedule_meetings',
                'can_create_announcements',
                'can_edit_announcements',
                'can_record_discipline',
                'can_view_discipline',
                'can_add_clubs',
                'can_manage_competitions',
                'can_manage_gatepass',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def user_count(self, obj):
        return obj.users.count()
    user_count.short_description = 'Number of Users'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'grade', 'house', 'is_staff']
    list_filter = ['role', 'grade', 'house', 'is_staff', 'is_active', 'is_phase_head']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone', 'avatar', 'bio')}),
        ('Role & Academic Info', {'fields': ('role', 'grade', 'section', 'house', 'is_phase_head')}),
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


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['subject', 'name', 'email', 'status_badge', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'email', 'username', 'subject', 'message']
    readonly_fields = ['name', 'email', 'username', 'subject', 'message', 'ip_address', 'user_agent', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'username', 'created_at')
        }),
        ('Message', {
            'fields': ('subject', 'message')
        }),
        ('Status & Response', {
            'fields': ('status', 'admin_response', 'responded_by', 'responded_at')
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'pending': '#fbbf24',
            'in_progress': '#3b82f6',
            'resolved': '#10b981'
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def save_model(self, request, obj, form, change):
        if change and 'admin_response' in form.changed_data:
            obj.responded_by = request.user
            from django.utils import timezone
            obj.responded_at = timezone.now()
        super().save_model(request, obj, form, change)