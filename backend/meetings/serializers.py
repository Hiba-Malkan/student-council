from rest_framework import serializers
from .models import Meeting, MinutesOfMeeting, MeetingAttendance
from accounts.models import User


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user information for nested serialization"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class MinutesOfMeetingSerializer(serializers.ModelSerializer):
    uploaded_by_detail = UserBasicSerializer(source='uploaded_by', read_only=True)
    present_detail = UserBasicSerializer(source='present', many=True, read_only=True)
    absent_detail = UserBasicSerializer(source='absent', many=True, read_only=True)
    
    class Meta:
        model = MinutesOfMeeting
        fields = [
            'id', 'meeting', 'content', 'document', 'action_items',
            'present', 'present_detail', 'absent', 'absent_detail',
            'uploaded_by', 'uploaded_by_detail', 'uploaded_at',
            'emailed_to_phase_heads', 'email_sent_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'meeting', 'uploaded_by', 'uploaded_at', 'created_at', 'updated_at']


class MeetingSerializer(serializers.ModelSerializer):
    organized_by_detail = UserBasicSerializer(source='organized_by', read_only=True)
    attendees_detail = UserBasicSerializer(source='attendees', many=True, read_only=True)
    attendee_roles_detail = serializers.StringRelatedField(source='attendee_roles', many=True, read_only=True)
    mom = MinutesOfMeetingSerializer(read_only=True)
    has_mom = serializers.SerializerMethodField()
    is_past = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    
    class Meta:
        model = Meeting
        fields = [
            'id', 'title', 'description', 'date',
            'location', 'meeting_link', 
            'attendees', 'attendees_detail',
            'attendee_roles', 'attendee_roles_detail',
            'organized_by', 'organized_by_detail',
            'agenda', 'is_cancelled', 'cancellation_reason',
            'morning_reminder_sent',
            'mom', 'has_mom', 'is_past', 'can_delete',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'organized_by', 'morning_reminder_sent',
            'created_at', 'updated_at'
        ]
    
    def get_has_mom(self, obj):
        """Check if meeting has MOM"""
        return hasattr(obj, 'mom') and obj.mom is not None
    
    def get_is_past(self, obj):
        """Check if meeting date has passed"""
        from datetime import date
        return obj.date < date.today()
    
    def get_can_delete(self, obj):
        """Check if current user can delete this meeting"""
        request = self.context.get('request')
        if not request or not request.user:
            return False
        return (obj.organized_by == request.user or request.user.is_staff) and not self.get_is_past(obj)


class MeetingAttendanceSerializer(serializers.ModelSerializer):
    user_detail = UserBasicSerializer(source='user', read_only=True)
    meeting_detail = serializers.StringRelatedField(source='meeting', read_only=True)
    marked_by_detail = UserBasicSerializer(source='marked_by', read_only=True)
    
    class Meta:
        model = MeetingAttendance
        fields = [
            'id', 'meeting', 'meeting_detail', 'user', 'user_detail',
            'status', 'notes', 'marked_by', 'marked_by_detail',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['marked_by', 'created_at', 'updated_at']