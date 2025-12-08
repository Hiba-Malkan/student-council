from django.contrib import admin
from .models import Meeting, MinutesOfMeeting, MeetingAttendance


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ['title', 'date', 'location', 'organized_by', 'is_cancelled', 'has_mom']
    list_filter = ['date', 'is_cancelled', 'organized_by']
    search_fields = ['title', 'description', 'location']
    date_hierarchy = 'date'
    filter_horizontal = ['attendees', 'attendee_roles']
    list_per_page = 50
    
    fieldsets = (
        ('Meeting Information', {
            'fields': ('title', 'description', 'organized_by')
        }),
        ('Schedule', {
            'fields': ('date', 'location', 'meeting_link')
        }),
        ('Attendees', {
            'fields': ('attendees', 'attendee_roles')
        }),
        ('Agenda', {
            'fields': ('agenda',)
        }),
        ('Status', {
            'fields': ('is_cancelled', 'cancellation_reason')
        }),
        ('Reminders', {
            'fields': ('morning_reminder_sent',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def has_mom(self, obj):
        """Check if meeting has MOM uploaded"""
        return hasattr(obj, 'mom') and obj.mom is not None
    has_mom.boolean = True
    has_mom.short_description = 'MOM Uploaded'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('organized_by').prefetch_related('attendees', 'attendee_roles')


@admin.register(MinutesOfMeeting)
class MinutesOfMeetingAdmin(admin.ModelAdmin):
    list_display = ['get_meeting_title', 'get_meeting_date', 'uploaded_by', 'uploaded_at', 'emailed_to_phase_heads', 'has_document']
    list_filter = ['uploaded_at', 'emailed_to_phase_heads', 'meeting__date']
    search_fields = ['meeting__title', 'content', 'action_items']
    readonly_fields = ['uploaded_at', 'created_at', 'updated_at']
    filter_horizontal = ['present', 'absent']
    date_hierarchy = 'uploaded_at'
    list_per_page = 50
    
    fieldsets = (
        ('Meeting', {'fields': ('meeting',)}),
        ('Content', {'fields': ('content', 'document', 'action_items')}),
        ('Attendance', {'fields': ('present', 'absent')}),
        ('Upload Information', {'fields': ('uploaded_by', 'uploaded_at')}),
        ('Email Status', {'fields': ('emailed_to_phase_heads', 'email_sent_at')}),
    )
    
    def get_meeting_title(self, obj):
        return obj.meeting.title
    get_meeting_title.short_description = 'Meeting'
    get_meeting_title.admin_order_field = 'meeting__title'
    
    def get_meeting_date(self, obj):
        return obj.meeting.date
    get_meeting_date.short_description = 'Meeting Date'
    get_meeting_date.admin_order_field = 'meeting__date'
    
    def has_document(self, obj):
        return bool(obj.document)
    has_document.boolean = True
    has_document.short_description = 'Document'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('meeting', 'uploaded_by').prefetch_related('present', 'absent')


@admin.register(MeetingAttendance)
class MeetingAttendanceAdmin(admin.ModelAdmin):
    list_display = ['get_meeting_title', 'get_meeting_date', 'user', 'status', 'marked_by']
    list_filter = ['status', 'meeting__date', 'meeting']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'meeting__title']
    date_hierarchy = 'meeting__date'
    list_per_page = 100
    
    fieldsets = (
        ('Meeting & User', {'fields': ('meeting', 'user')}),
        ('Attendance', {'fields': ('status', 'notes')}),
        ('Marked By', {'fields': ('marked_by',)}),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_meeting_title(self, obj):
        return obj.meeting.title
    get_meeting_title.short_description = 'Meeting'
    get_meeting_title.admin_order_field = 'meeting__title'
    
    def get_meeting_date(self, obj):
        return obj.meeting.date
    get_meeting_date.short_description = 'Date'
    get_meeting_date.admin_order_field = 'meeting__date'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('meeting', 'user', 'marked_by')
