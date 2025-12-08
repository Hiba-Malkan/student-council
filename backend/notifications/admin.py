from django.contrib import admin
from .models import Notification, NotificationPreference, EmailTemplate, NotificationBatch


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'notification_type', 'title', 'is_read', 'send_email', 'email_sent', 'created_at']
    list_filter = ['notification_type', 'is_read', 'is_snoozed', 'send_email', 'email_sent', 'created_at']
    search_fields = ['recipient__username', 'title', 'message']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Notification Information', {
            'fields': ('recipient', 'notification_type', 'title', 'message')
        }),
        ('Content Object', {
            'fields': ('content_type', 'object_id', 'action_url')
        }),
        ('Status', {
            'fields': ('is_read', 'read_at', 'is_snoozed', 'snoozed_until')
        }),
        ('Email', {
            'fields': ('send_email', 'email_sent', 'email_sent_at')
        }),
    )
    
    readonly_fields = ['read_at', 'email_sent_at', 'created_at']


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
            'fields': ('body_template', 'available_variables')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(NotificationBatch)
class NotificationBatchAdmin(admin.ModelAdmin):
    list_display = ['batch_type', 'sent_to_count', 'sent_at']
    list_filter = ['batch_type', 'sent_at']
    search_fields = ['batch_type']
    readonly_fields = ['sent_at']
    
    fieldsets = (
        ('Batch Information', {
            'fields': ('batch_type', 'sent_to_count', 'metadata')
        }),
    )