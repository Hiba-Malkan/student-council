from django.contrib import admin
from django.utils.html import format_html
from .models import Club


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'status_badge',
        'member_count',
        'established_year',
        'logo_preview',
        'created_at',
    ]
    list_filter = ['status', 'established_year', 'created_at']
    search_fields = ['name', 'description', 'established_by', 'tutors']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'logo_preview_large']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'status')
        }),
        ('Logo', {
            'fields': ('logo', 'logo_preview_large')
        }),
        ('Membership & History', {
            'fields': (
                'member_count',
                'established_year',
                'established_by',
                'tutors',
            )
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """Display status as a colored badge"""
        colors = {
            'active': '#10b981',
            'under_review': '#f59e0b',
            'inactive': '#6b7280',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            colors.get(obj.status, '#6b7280'),
            obj.get_status_display().upper()
        )
    status_badge.short_description = 'Status'
    
    def logo_preview(self, obj):
        """Small logo preview in list view"""
        if obj.logo:
            return format_html(
                '<img src="{}" style="width: 40px; height: 40px; '
                'object-fit: cover; border-radius: 8px;" />',
                obj.logo.url
            )
        return '—'
    logo_preview.short_description = 'Logo'
    
    def logo_preview_large(self, obj):
        """Large logo preview in detail view"""
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 300px; '
                'object-fit: contain; border-radius: 12px; border: 1px solid #e5e7eb;" />',
                obj.logo.url
            )
        return 'No logo uploaded'
    logo_preview_large.short_description = 'Logo Preview'