from rest_framework import serializers
from .models import GatePass
from accounts.serializers import UserSerializer

class GatePassSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    approved_by = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = GatePass
        fields = ['id', 'student', 'reason', 'status', 'status_display', 'approved_by', 'approval_note', 'approval_timestamp', 'requested_at', 'updated_at']
        read_only_fields = ['id', 'student', 'approved_by', 'approval_note', 'approval_timestamp', 'requested_at', 'updated_at']

class GatePassApprovalSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['approved', 'denied'])
    note = serializers.CharField(required=False, allow_blank=True)
    
    def validate_status(self, value):
        if value not in ['approved', 'denied']:
            raise serializers.ValidationError("Status must be 'approved' or 'denied'")
        return value
