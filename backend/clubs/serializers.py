from rest_framework import serializers
from accounts.models import User
from .models import Club


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user information for nested serialization"""
    full_name = serializers.SerializerMethodField()
    role_name = serializers.CharField(source='role.name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'full_name',
            'email',
            'role_name',
        ]
    
    def get_full_name(self, obj):
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        return obj.username


class ClubListSerializer(serializers.ModelSerializer):
    """Serializer for listing clubs"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    logo_url = serializers.SerializerMethodField()
    founders_list = serializers.ReadOnlyField()
    tutors_list = serializers.ReadOnlyField()
    
    class Meta:
        model = Club
        fields = [
            'id',
            'name',
            'description',
            'logo_url',
            'member_count',
            'established_year',
            'established_by',
            'founders_list',
            'tutors',
            'tutors_list',
            'status',
            'created_by_name',
            'created_at',
        ]
    
    def get_logo_url(self, obj):
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None


class ClubDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for a single club"""
    created_by_detail = UserBasicSerializer(source='created_by', read_only=True)
    logo_url = serializers.SerializerMethodField()
    founders_list = serializers.ReadOnlyField()
    tutors_list = serializers.ReadOnlyField()
    
    class Meta:
        model = Club
        fields = [
            'id',
            'name',
            'description',
            'logo_url',
            'member_count',
            'established_year',
            'established_by',
            'founders_list',
            'tutors',
            'tutors_list',
            'status',
            'created_by_detail',
            'created_at',
            'updated_at',
        ]
    
    def get_logo_url(self, obj):
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None


class ClubCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating clubs"""
    
    class Meta:
        model = Club
        fields = [
            'id',
            'name',
            'description',
            'logo',
            'member_count',
            'established_year',
            'established_by',
            'tutors',
            'status',
        ]
        read_only_fields = ['id']
    
    def create(self, validated_data):
        # Set the created_by field from the request user
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)