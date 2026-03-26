from django.contrib import admin
from .models import Competition, CompetitionSignup


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'hosted_by', 'participant_count', 'event_date', 
        'is_active', 'created_by', 'created_at'
    ]
    list_filter = ['is_active', 'event_date', 'created_at']
    search_fields = ['name', 'hosted_by', 'participants', 'description', 'additional_info']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'hosted_by', 'participants', 'participant_count', 'is_active')
        }),
        ('Event Details', {
            'fields': ('event_date', 'event_time', 'location', 'team_size')
        }),
        ('Content', {
            'fields': ('description', 'additional_info', 'event_link', 'brochure')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CompetitionSignup)
class CompetitionSignupAdmin(admin.ModelAdmin):
    list_display = [
        'student_name',
        'email',
        'competition',
        'phone',
        'team_name',
        'created_at',
    ]
    list_filter = ['competition', 'created_at']
    search_fields = ['student_name', 'email', 'phone', 'team_name']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('student_name', 'email', 'phone')
        }),
        ('Competition Information', {
            'fields': ('competition', 'team_name')
        }),
        ('Message', {
            'fields': ('message',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Prevent manual creation - signups come from public form only"""
        return False
