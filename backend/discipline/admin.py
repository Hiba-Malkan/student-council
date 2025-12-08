from django.contrib import admin
from .models import DisciplineOffence, OffenceType, DefaulterReport, DisciplineAction


@admin.register(OffenceType)
class OffenceTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'severity', 'points', 'offence_count', 'created_at']
    list_filter = ['severity']
    search_fields = ['name', 'description']
    
    def offence_count(self, obj):
        return obj.offences.count()
    offence_count.short_description = 'Number of Offences'


@admin.register(DisciplineOffence)
class DisciplineOffenceAdmin(admin.ModelAdmin):
    list_display = ['student', 'offence_type', 'date', 'status', 'recorded_by', 'reviewed_by']
    list_filter = ['status', 'date', 'offence_type', 'parent_notified']
    search_fields = ['student__username', 'student__first_name', 'student__last_name', 'description']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Offence Information', {
            'fields': ('student', 'offence_type', 'date', 'location')
        }),
        ('Details', {
            'fields': ('description', 'photo')
        }),
        ('Recorded By', {
            'fields': ('recorded_by',)
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Review', {
            'fields': ('reviewed_by', 'reviewed_at', 'review_notes')
        }),
        ('Action Taken', {
            'fields': ('action_taken', 'parent_notified', 'parent_notification_date')
        }),
    )
    
    readonly_fields = ['time', 'reviewed_at', 'created_at', 'updated_at']


@admin.register(DefaulterReport)
class DefaulterReportAdmin(admin.ModelAdmin):
    list_display = ['date', 'phase', 'defaulter_count', 'sent_to_phase_heads', 'generated_at']
    list_filter = ['date', 'phase', 'sent_to_phase_heads']
    filter_horizontal = ['defaulters']
    readonly_fields = ['generated_at', 'email_sent_at']
    
    fieldsets = (
        ('Report Information', {
            'fields': ('date', 'phase')
        }),
        ('Defaulters', {
            'fields': ('defaulters',)
        }),
        ('Email Status', {
            'fields': ('sent_to_phase_heads', 'email_sent_at')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )
    
    def defaulter_count(self, obj):
        return obj.defaulters.count()
    defaulter_count.short_description = 'Number of Defaulters'


@admin.register(DisciplineAction)
class DisciplineActionAdmin(admin.ModelAdmin):
    list_display = ['offence', 'action_type', 'date_assigned', 'date_completed', 'is_completed', 'assigned_by']
    list_filter = ['action_type', 'is_completed', 'date_assigned']
    search_fields = ['offence__student__username', 'description']
    
    fieldsets = (
        ('Offence', {
            'fields': ('offence',)
        }),
        ('Action', {
            'fields': ('action_type', 'description')
        }),
        ('Dates', {
            'fields': ('date_assigned', 'date_completed', 'is_completed')
        }),
        ('Assigned By', {
            'fields': ('assigned_by',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']