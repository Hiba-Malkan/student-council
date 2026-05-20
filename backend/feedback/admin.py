from django.contrib import admin
from django.utils.html import format_html
from .models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = [
        'subject',
        'type_badge',
        'priority_badge',
        'status_badge',
        'submitter_name_display',
        'created_at',
        'assigned_to'
    ]
    
    list_filter = ['type', 'status', 'priority', 'category', 'created_at']
    search_fields = ['subject', 'description', 'name', 'email', 'submitted_by__username']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Submission Info', {
            'fields': ('submitted_by', 'name', 'email')
        }),
        ('Feedback Details', {
            'fields': ('type', 'category', 'subject', 'description', 'screenshot')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority', 'assigned_to')
        }),
        ('Admin Notes', {
            'fields': ('admin_notes', 'resolved_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def type_badge(self, obj):
        colors = {
            'FEEDBACK': '#3498db',
            'BUG': '#e74c3c',
            'FEATURE_REQUEST': '#2ecc71',
            'PERFORMANCE': '#f39c12',
            'OTHER': '#95a5a6',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            colors.get(obj.type, '#95a5a6'),
            obj.get_type_display()
        )
    type_badge.short_description = 'Type'
    
    def priority_badge(self, obj):
        colors = {
            'LOW': '#95a5a6',
            'MEDIUM': '#3498db',
            'HIGH': '#f39c12',
            'CRITICAL': '#e74c3c',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            colors.get(obj.priority, '#95a5a6'),
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'
    
    def status_badge(self, obj):
        colors = {
            'OPEN': '#3498db',
            'IN_PROGRESS': '#f39c12',
            'RESOLVED': '#2ecc71',
            'CLOSED': '#95a5a6',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            colors.get(obj.status, '#95a5a6'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def submitter_name_display(self, obj):
        return obj.submitter_name
    submitter_name_display.short_description = 'Submitted By'
