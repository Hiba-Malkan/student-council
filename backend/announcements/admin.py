from django.contrib import admin
from .models import Announcement, EventParticipant, AnnouncementRead


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'announcement_type', 'created_by', 'is_published', 'is_pinned', 'created_at']
    list_filter = ['announcement_type', 'is_published', 'is_pinned', 'is_public', 'created_at']
    search_fields = ['title', 'content']
    date_hierarchy = 'created_at'
    filter_horizontal = ['target_roles', 'target_users']
    
    fieldsets = (
        ('Announcement Information', {
            'fields': ('title', 'content', 'announcement_type', 'created_by')
        }),
        ('Targeting', {
            'fields': ('target_roles', 'target_users', 'target_houses', 'target_grades', 'is_public')
        }),
        ('Event Details (if applicable)', {
            'fields': ('event_date', 'event_time', 'event_location', 'registration_required', 'registration_deadline')
        }),
        ('Attachments', {
            'fields': ('attachments',)
        }),
        ('Publishing', {
            'fields': ('is_published', 'published_at', 'is_pinned')
        }),
        ('Email Notification', {
            'fields': ('send_email', 'email_sent', 'email_sent_at')
        }),
    )
    
    readonly_fields = ['published_at', 'email_sent', 'email_sent_at', 'created_at', 'updated_at']


@admin.register(EventParticipant)
class EventParticipantAdmin(admin.ModelAdmin):
    list_display = ['announcement', 'user', 'status', 'role_in_event', 'is_confirmed', 'registered_at']
    list_filter = ['status', 'is_confirmed', 'registered_at']
    search_fields = ['announcement__title', 'user__username', 'role_in_event']
    
    fieldsets = (
        ('Event & User', {
            'fields': ('announcement', 'user')
        }),
        ('Participation', {
            'fields': ('role_in_event', 'status', 'is_confirmed')
        }),
        ('Assignment', {
            'fields': ('assigned_by', 'notes')
        }),
    )
    
    readonly_fields = ['registered_at', 'created_at', 'updated_at']


@admin.register(AnnouncementRead)
class AnnouncementReadAdmin(admin.ModelAdmin):
    list_display = ['announcement', 'user', 'read_at']
    list_filter = ['read_at']
    search_fields = ['announcement__title', 'user__username']
    readonly_fields = ['read_at']