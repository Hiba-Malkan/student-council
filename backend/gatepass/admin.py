from django.contrib import admin
from .models import GatePass

@admin.register(GatePass)
class GatePassAdmin(admin.ModelAdmin):
    list_display = ['id', 'student', 'status', 'requested_at', 'approved_by']
    list_filter = ['status', 'requested_at']
    search_fields = ['student__username', 'student__email']
    readonly_fields = ['requested_at', 'updated_at', 'approval_timestamp']
