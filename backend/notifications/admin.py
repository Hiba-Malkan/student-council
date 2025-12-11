from django.contrib import admin
from .models import Notification, NotificationPreference, EmailTemplate


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'notification_type', 'title', 'is_read', 'send_email', 'email_sent', 'created_at']
    list_filter = ['notification_type', 'is_read', 'is_snoozed', 'send_email', 'email_sent', 'created_at']
    search_fields = ['recipient__username', 'recipient__first_name', 'recipient__last_name', 'title', 'message']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Notification Information', {
            'fields': ('recipient', 'notification_type', 'title', 'message')
        }),
        ('Content Object', {
            'fields': ('content_type', 'object_id', 'action_url'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_read', 'read_at', 'is_snoozed', 'snoozed_until')
        }),
        ('Email', {
            'fields': ('send_email', 'email_sent', 'email_sent_at')
        }),
    )
    
    readonly_fields = ['read_at', 'email_sent_at', 'created_at']
    
    actions = ['mark_as_read', 'mark_as_unread', 'send_emails']
    
    def mark_as_read(self, request, queryset):
        from django.utils import timezone
        count = queryset.update(is_read=True, read_at=timezone.now())
        self.message_user(request, f'{count} notification(s) marked as read.')
    mark_as_read.short_description = 'Mark selected notifications as read'
    
    def mark_as_unread(self, request, queryset):
        count = queryset.update(is_read=False, read_at=None)
        self.message_user(request, f'{count} notification(s) marked as unread.')
    mark_as_unread.short_description = 'Mark selected notifications as unread'
    
    def send_emails(self, request, queryset):
        from .utils import send_notification_email
        count = 0
        for notification in queryset.filter(send_email=True, email_sent=False):
            if send_notification_email(notification):
                count += 1
        self.message_user(request, f'{count} email(s) sent successfully.')
    send_emails.short_description = 'Send pending emails for selected notifications'


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'email_for_meetings', 'email_for_announcements', 'daily_digest', 'weekly_digest']
    list_filter = ['email_for_meetings', 'email_for_announcements', 'daily_digest', 'weekly_digest']
    search_fields = ['user__username']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Email Preferences', {
            'fields': (
                'email_for_meetings',
                'email_for_announcements',
                'email_for_duties',
                'email_for_discipline',
                'email_for_projects',
            )
        }),
        ('In-App Preferences', {
            'fields': (
                'in_app_for_meetings',
                'in_app_for_announcements',
                'in_app_for_duties',
                'in_app_for_discipline',
                'in_app_for_projects',
            )
        }),
        ('Digest Preferences', {
            'fields': ('daily_digest', 'weekly_digest')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'subject', 'body_template']
    
    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'subject', 'is_active')
        }),
        ('Template Body', {
            'fields': ('body_template', 'available_variables'),
            'description': 'Use variables like {{user_name}}, {{title}}, {{date}}, {{time}}, {{location}}'
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']