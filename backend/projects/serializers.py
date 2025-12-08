from rest_framework import serializers
from .models import Project, ProjectAttachment, ProjectMilestone, ProjectUpdate, Purchase
from accounts.serializers import UserSerializer


class ProjectAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_detail = UserSerializer(source='uploaded_by', read_only=True)
    
    class Meta:
        model = ProjectAttachment
        fields = [
            'id', 'project', 'title', 'file', 'file_type',
            'uploaded_by', 'uploaded_by_detail', 'created_at'
        ]
        read_only_fields = ['uploaded_by', 'created_at']


class ProjectMilestoneSerializer(serializers.ModelSerializer):
    assigned_to_detail = UserSerializer(source='assigned_to', read_only=True)
    
    class Meta:
        model = ProjectMilestone
        fields = [
            'id', 'project', 'title', 'description', 'due_date',
            'is_completed', 'completed_at', 'assigned_to',
            'assigned_to_detail', 'created_at', 'updated_at'
        ]
        read_only_fields = ['completed_at', 'created_at', 'updated_at']


class ProjectUpdateSerializer(serializers.ModelSerializer):
    posted_by_detail = UserSerializer(source='posted_by', read_only=True)
    
    class Meta:
        model = ProjectUpdate
        fields = [
            'id', 'project', 'title', 'content', 'posted_by',
            'posted_by_detail', 'created_at'
        ]
        read_only_fields = ['posted_by', 'created_at']


class PurchaseSerializer(serializers.ModelSerializer):
    purchased_by_detail = UserSerializer(source='purchased_by', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Purchase
        fields = [
            'id', 'project', 'item_name', 'description', 'quantity',
            'unit_price', 'total_price', 'vendor', 'purchase_date',
            'status', 'status_display', 'receipt', 'purchased_by',
            'purchased_by_detail', 'created_at', 'updated_at'
        ]
        read_only_fields = ['total_price', 'purchased_by', 'created_at', 'updated_at']


class ProjectSerializer(serializers.ModelSerializer):
    proposed_by_detail = UserSerializer(source='proposed_by', read_only=True)
    assigned_to_detail = UserSerializer(source='assigned_to', many=True, read_only=True)
    approved_by_detail = UserSerializer(source='approved_by', read_only=True)
    project_type_display = serializers.CharField(source='get_project_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    attachments = ProjectAttachmentSerializer(many=True, read_only=True)
    milestones = ProjectMilestoneSerializer(many=True, read_only=True)
    updates = ProjectUpdateSerializer(many=True, read_only=True)
    purchases = PurchaseSerializer(many=True, read_only=True)
    total_spent = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'title', 'description', 'project_type',
            'project_type_display', 'estimated_budget', 'actual_cost',
            'proposal_date', 'deadline', 'completion_date', 'status',
            'status_display', 'proposed_by', 'proposed_by_detail',
            'assigned_to', 'assigned_to_detail', 'approved_by',
            'approved_by_detail', 'approved_at', 'approval_notes',
            'rejection_reason', 'attachments', 'milestones', 'updates',
            'purchases', 'total_spent', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'proposal_date', 'proposed_by', 'approved_by', 'approved_at',
            'created_at', 'updated_at'
        ]
    
    def get_total_spent(self, obj):
        total = sum(purchase.total_price for purchase in obj.purchases.all())
        return float(total)