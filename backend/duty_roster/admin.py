from django.contrib import admin
from .models import Duty, DutyType


@admin.register(DutyType)
class DutyTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'color', 'duty_count', 'created_at']
    search_fields = ['name', 'description', 'location']
    list_filter = ['created_at']
    
    def duty_count(self, obj):
        return obj.duties.count()
    duty_count.short_description = 'Number of Duties'


@admin.register(Duty)
class DutyAdmin(admin.ModelAdmin):
    list_display = ['duty_type_name', 'assigned_to', 'date', 'location', 'subsidiary_area', 'is_completed', 'assigned_by']
    list_filter = ['duty_type', 'date', 'is_completed', 'assigned_by']
    search_fields = ['duty_type_name', 'assigned_to__username', 'assigned_to__first_name', 'assigned_to__last_name', 'location', 'subsidiary_area']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Duty Information', {
            'fields': ('duty_type', 'duty_type_name', 'assigned_to', 'assigned_by')
        }),
        ('Schedule & Location', {
            'fields': ('date', 'location', 'subsidiary_area')
        }),
        ('Details', {
            'fields': ('instructions', 'notes')
        }),
        ('Status', {
            'fields': ('is_completed', 'completed_at')
        }),
    )
    
    readonly_fields = ['completed_at', 'created_at', 'updated_at']
