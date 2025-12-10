from rest_framework import serializers
from .models import Competition


class CompetitionSerializer(serializers.ModelSerializer):
    """Serializer for competitions"""
    
    created_by_detail = serializers.SerializerMethodField()
    hosts_list = serializers.ReadOnlyField()
    participants_list = serializers.ReadOnlyField()
    
    class Meta:
        model = Competition
        fields = [
            'id', 'name', 'hosted_by', 'hosts_list', 'participants', 
            'participants_list', 'participant_count', 'event_link', 'brochure', 
            'additional_info', 'event_date', 'event_time', 'location', 'team_size', 
            'description', 'created_by', 'created_by_detail', 'created_at', 
            'updated_at', 'is_active'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def get_created_by_detail(self, obj):
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'username': obj.created_by.username,
                'first_name': obj.created_by.first_name,
                'last_name': obj.created_by.last_name,
            }
        return None
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class CompetitionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for competition list view"""
    
    hosts_list = serializers.ReadOnlyField()
    participants_list = serializers.ReadOnlyField()
    
    class Meta:
        model = Competition
        fields = [
            'id', 'name', 'hosted_by', 'hosts_list', 'participants',
            'participants_list', 'participant_count', 'event_link', 'brochure',
            'additional_info', 'event_date', 'event_time', 'location', 
            'team_size', 'description', 'is_active'
        ]