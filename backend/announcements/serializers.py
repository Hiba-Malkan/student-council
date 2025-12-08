from rest_framework import serializers
from .models import Announcement, EventParticipant, AnnouncementRead
from accounts.serializers import UserSerializer, RoleSerializer


class AnnouncementSerializer(serializers.ModelSerializer):
    target_roles_detail = RoleSerializer(source='target_roles', many=True, read_only=True)
    target_users_detail = UserSerializer(source='target_users', many=True, read_only=True)
    created_by_detail = UserSerializer(source='created_by', read_only=True)
    announcement_type_display = serializers.CharField(source='get_announcement_type_display', read_only=True)
    participant_count = serializers.SerializerMethodField()
    is_read_by_user = serializers.SerializerMethodField()
    
    class Meta:
        model = Announcement
        fields = [
            'id', 'title', 'content', 'announcement_type',
            'announcement_type_display', 'target_roles', 'target_roles_detail',
            'target_users', 'target_users_detail', 'target_houses',
            'target_grades', 'is_public', 'event_date', 'event_time',
            'event_location', 'registration_required', 'registration_deadline',
            'attachments', 'created_by', 'created_by_detail', 'is_published',
            'published_at', 'send_email', 'email_sent', 'email_sent_at',
            'is_pinned', 'participant_count', 'is_read_by_user',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'created_by', 'published_at', 'email_sent', 'email_sent_at',
            'created_at', 'updated_at'
        ]
    
    def get_participant_count(self, obj):
        if obj.announcement_type == 'EVENT':
            return obj.participants.count()
        return None
    
    def get_is_read_by_user(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return AnnouncementRead.objects.filter(
                announcement=obj,
                user=request.user
            ).exists()
        return False
    
    def create(self, validated_data):
        """Handle creation with proper field handling"""
        # Extract many-to-many fields
        target_roles = validated_data.pop('target_roles', [])
        target_users = validated_data.pop('target_users', [])
        
        # Create the announcement
        announcement = Announcement.objects.create(**validated_data)
        
        # Set many-to-many relationships
        if target_roles:
            announcement.target_roles.set(target_roles)
        if target_users:
            announcement.target_users.set(target_users)
        
        return announcement
    
    def update(self, instance, validated_data):
        """Handle updates with proper field handling"""
        # Extract many-to-many fields
        target_roles = validated_data.pop('target_roles', None)
        target_users = validated_data.pop('target_users', None)
        
        # Update simple fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update many-to-many relationships if provided
        if target_roles is not None:
            instance.target_roles.set(target_roles)
        if target_users is not None:
            instance.target_users.set(target_users)
        
        return instance


class EventParticipantSerializer(serializers.ModelSerializer):
    announcement_detail = AnnouncementSerializer(source='announcement', read_only=True)
    user_detail = UserSerializer(source='user', read_only=True)
    assigned_by_detail = UserSerializer(source='assigned_by', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = EventParticipant
        fields = [
            'id', 'announcement', 'announcement_detail', 'user', 'user_detail',
            'registered_at', 'is_confirmed', 'assigned_by', 'assigned_by_detail',
            'role_in_event', 'status', 'status_display', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['registered_at', 'assigned_by', 'created_at', 'updated_at']


class AnnouncementReadSerializer(serializers.ModelSerializer):
    announcement_detail = AnnouncementSerializer(source='announcement', read_only=True)
    user_detail = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = AnnouncementRead
        fields = ['id', 'announcement', 'announcement_detail', 'user', 'user_detail', 'read_at']
        read_only_fields = ['read_at']