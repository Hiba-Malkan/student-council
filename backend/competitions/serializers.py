from rest_framework import serializers
from .models import Competition, CompetitionSignup


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


class CompetitionSignupSerializer(serializers.ModelSerializer):
    """Serializer for competition signups"""
    
    class Meta:
        model = CompetitionSignup
        fields = [
            'id',
            'competition',
            'student_name',
            'email',
            'phone',
            'team_name',
            'message',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def create(self, validated_data):
        # Handle duplicate email for same competition - update instead of create
        competition = validated_data.get('competition')
        email = validated_data.get('email')
        
        signup, created = CompetitionSignup.objects.update_or_create(
            competition=competition,
            email=email,
            defaults={
                'student_name': validated_data.get('student_name'),
                'phone': validated_data.get('phone', ''),
                'team_name': validated_data.get('team_name', ''),
                'message': validated_data.get('message', ''),
            }
        )
        return signup