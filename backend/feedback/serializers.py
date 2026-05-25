from rest_framework import serializers
from .models import Feedback


class FeedbackListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing feedback"""
    submitted_by_name = serializers.CharField(source='submitter_name', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = Feedback
        fields = [
            'id',
            'type',
            'type_display',
            'subject',
            'description',
            'status',
            'status_display',
            'priority',
            'priority_display',
            'submitted_by_name',
            'created_at',
            'assigned_to',
            'email',
            'category'
        ]
        read_only_fields = fields


class FeedbackDetailSerializer(serializers.ModelSerializer):
    """Full serializer for feedback detail view"""
    submitted_by_name = serializers.CharField(source='submitter_name', read_only=True)
    submitted_by_username = serializers.CharField(source='submitted_by.username', read_only=True, required=False)
    submitted_by_role = serializers.CharField(source='submitted_by.role.name', read_only=True, required=False, allow_null=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True, required=False)
    
    class Meta:
        model = Feedback
        fields = [
            'id',
            'submitted_by',
            'submitted_by_name',
            'submitted_by_username',
            'submitted_by_role',
            'name',
            'email',
            'type',
            'type_display',
            'category',
            'subject',
            'description',
            'screenshot',
            'status',
            'status_display',
            'priority',
            'priority_display',
            'admin_notes',
            'assigned_to',
            'assigned_to_name',
            'created_at',
            'updated_at',
            'resolved_at',
        ]
        read_only_fields = [
            'id',
            'submitted_by',
            'admin_notes',
            'assigned_to',
            'resolved_at',
            'created_at',
            'updated_at',
            'type_display',
            'status_display',
            'priority_display',
            'submitted_by_name',
            'submitted_by_username',
            'submitted_by_role',
            'assigned_to_name',
        ]


class FeedbackCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new feedback (public endpoint)"""
    
    class Meta:
        model = Feedback
        fields = [
            'name',
            'email',
            'type',
            'priority',
            'category',
            'subject',
            'description',
            'screenshot',
        ]
    
    def create(self, validated_data):
        """Set submitted_by to current user if authenticated"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['submitted_by'] = request.user
        
        return super().create(validated_data)
