from rest_framework import serializers
from .models import Duty, DutyType
from accounts.serializers import UserSerializer


class DutyTypeSerializer(serializers.ModelSerializer):
    duty_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DutyType
        fields = [
            'id', 'name', 'description', 'location', 'color',
            'duty_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_duty_count(self, obj):
        return obj.duties.count()


class DutySerializer(serializers.ModelSerializer):
    duty_type_detail = DutyTypeSerializer(source='duty_type', read_only=True)
    assigned_to_detail = UserSerializer(source='assigned_to', read_only=True)
    assigned_by_detail = UserSerializer(source='assigned_by', read_only=True)
    
    class Meta:
        model = Duty
        fields = [
            'id', 'duty_type', 'duty_type_detail', 'duty_type_name',
            'assigned_to', 'assigned_to_detail', 'date',
            'location', 'subsidiary_area', 'instructions',
            'is_completed', 'completed_at', 'notes',
            'assigned_by', 'assigned_by_detail',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['completed_at', 'created_at', 'updated_at']