from rest_framework import serializers
from .models import Notification, NotificationPreference, EmailTemplate
from accounts.serializers import UserSerializer


class NotificationSerializer(serializers.ModelSerializer):
    recipient_detail = UserSerializer(source='recipient', read_only=True)
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'recipient_detail', 'notification_type',
            'notification_type_display', 'title', 'message',
            'content_type', 'object_id', 'action_url', 'is_read',
            'read_at', 'is_snoozed', 'snoozed_until', 'send_email',
            'email_sent', 'email_sent_at', 'created_at'
        ]
        read_only_fields = ['read_at', 'email_sent', 'email_sent_at', 'created_at']


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    user_detail = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = NotificationPreference
        fields = [
            'id', 'user', 'user_detail', 'email_for_meetings',
            'email_for_announcements', 'email_for_duties',
            'email_for_discipline', 'email_for_competitions',
            'in_app_for_meetings', 'in_app_for_announcements',
            'in_app_for_duties', 'in_app_for_discipline',
            'in_app_for_competitions', 'daily_digest', 'weekly_digest',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']


class EmailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailTemplate
        fields = [
            'id', 'name', 'subject', 'body_template',
            'available_variables', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']