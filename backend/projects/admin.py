from django.contrib import admin
from .models import Project, ProjectAttachment, ProjectMilestone, ProjectUpdate, Purchase


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'project_type', 'status', 'deadline', 'proposed_by', 'approved_by']
    list_filter = ['project_type', 'status', 'deadline', 'created_at']
    search_fields = ['title', 'description']
    date_hierarchy = 'deadline'
    filter_horizontal = ['assigned_to']
    
    fieldsets = (
        ('Project Information', {
            'fields': ('title', 'description', 'project_type')
        }),
        ('Budget', {
            'fields': ('estimated_budget', 'actual_cost')
        }),
        ('Timeline', {
            'fields': ('deadline', 'completion_date')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('People', {
            'fields': ('proposed_by', 'assigned_to')
        }),
        ('Approval', {
            'fields': ('approved_by', 'approved_at', 'approval_notes', 'rejection_reason')
        }),
    )
    
    readonly_fields = ['proposal_date', 'approved_at', 'created_at', 'updated_at']


@admin.register(ProjectAttachment)
class ProjectAttachmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'file_type', 'uploaded_by', 'created_at']
    list_filter = ['file_type', 'created_at']
    search_fields = ['title', 'project__title']
    
    fieldsets = (
        ('Attachment Information', {
            'fields': ('project', 'title', 'file', 'file_type')
        }),
        ('Upload Info', {
            'fields': ('uploaded_by',)
        }),
    )
    
    readonly_fields = ['created_at']


@admin.register(ProjectMilestone)
class ProjectMilestoneAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'due_date', 'is_completed', 'assigned_to']
    list_filter = ['is_completed', 'due_date']
    search_fields = ['title', 'project__title']
    date_hierarchy = 'due_date'
    
    fieldsets = (
        ('Milestone Information', {
            'fields': ('project', 'title', 'description')
        }),
        ('Schedule', {
            'fields': ('due_date', 'assigned_to')
        }),
        ('Status', {
            'fields': ('is_completed', 'completed_at')
        }),
    )
    
    readonly_fields = ['completed_at', 'created_at', 'updated_at']


@admin.register(ProjectUpdate)
class ProjectUpdateAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'posted_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title', 'content', 'project__title']
    
    fieldsets = (
        ('Update Information', {
            'fields': ('project', 'title', 'content', 'posted_by')
        }),
    )
    
    readonly_fields = ['created_at']


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['item_name', 'project', 'quantity', 'unit_price', 'total_price', 'status', 'purchased_by']
    list_filter = ['status', 'purchase_date']
    search_fields = ['item_name', 'project__title', 'vendor']
    
    fieldsets = (
        ('Purchase Information', {
            'fields': ('project', 'item_name', 'description')
        }),
        ('Pricing', {
            'fields': ('quantity', 'unit_price', 'total_price')
        }),
        ('Vendor', {
            'fields': ('vendor', 'purchase_date')
        }),
        ('Status', {
            'fields': ('status', 'receipt', 'purchased_by')
        }),
    )
    
    readonly_fields = ['total_price', 'created_at', 'updated_at']