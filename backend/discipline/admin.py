from django.contrib import admin
from .models import DisciplineRecord


@admin.register(DisciplineRecord)
class DisciplineRecordAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'dno', 'class_section', 'offense_count', 'created_by', 'created_at']
    list_filter = ['class_section', 'offense_count', 'created_at']
    search_fields = ['student_name', 'dno', 'class_section']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Student Information', {
            'fields': ('student_name', 'class_section', 'dno')
        }),
        ('Offense Details', {
            'fields': ('offense_count',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new record
            obj.created_by = request.user
        super().save_model(request, obj, form, change)