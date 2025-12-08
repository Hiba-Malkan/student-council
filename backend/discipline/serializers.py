from rest_framework import serializers
from .models import DisciplineOffence, OffenceType, DefaulterReport, DisciplineAction
from accounts.serializers import UserSerializer


class OffenceTypeSerializer(serializers.ModelSerializer):
    offence_count = serializers.SerializerMethodField()
    
    class Meta:
        model = OffenceType
        fields = [
            'id', 'name', 'description', 'severity', 'points',
            'offence_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_offence_count(self, obj):
        return obj.offences.count()


class DisciplineOffenceSerializer(serializers.ModelSerializer):
    student_detail = UserSerializer(source='student', read_only=True)
    offence_type_detail = OffenceTypeSerializer(source='offence_type', read_only=True)
    recorded_by_detail = UserSerializer(source='recorded_by', read_only=True)
    reviewed_by_detail = UserSerializer(source='reviewed_by', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = DisciplineOffence
        fields = [
            'id', 'student', 'student_detail', 'offence_type',
            'offence_type_detail', 'date', 'time', 'location',
            'description', 'photo', 'recorded_by', 'recorded_by_detail',
            'status', 'status_display', 'reviewed_by', 'reviewed_by_detail',
            'reviewed_at', 'review_notes', 'action_taken', 'parent_notified',
            'parent_notification_date', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'time', 'recorded_by', 'reviewed_by', 'reviewed_at',
            'created_at', 'updated_at'
        ]


class DefaulterReportSerializer(serializers.ModelSerializer):
    defaulters_detail = UserSerializer(source='defaulters', many=True, read_only=True)
    defaulter_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DefaulterReport
        fields = [
            'id', 'date', 'phase', 'defaulters', 'defaulters_detail',
            'defaulter_count', 'generated_at', 'sent_to_phase_heads',
            'email_sent_at', 'notes'
        ]
        read_only_fields = ['generated_at', 'sent_to_phase_heads', 'email_sent_at']
    
    def get_defaulter_count(self, obj):
        return obj.defaulters.count()


class DisciplineActionSerializer(serializers.ModelSerializer):
    offence_detail = DisciplineOffenceSerializer(source='offence', read_only=True)
    assigned_by_detail = UserSerializer(source='assigned_by', read_only=True)
    action_type_display = serializers.CharField(source='get_action_type_display', read_only=True)
    
    class Meta:
        model = DisciplineAction
        fields = [
            'id', 'offence', 'offence_detail', 'action_type',
            'action_type_display', 'description', 'date_assigned',
            'date_completed', 'is_completed', 'assigned_by',
            'assigned_by_detail', 'created_at', 'updated_at'
        ]
        read_only_fields = ['assigned_by', 'created_at', 'updated_at']