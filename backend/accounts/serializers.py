from rest_framework import serializers
from .models import User, Role, UserSession


class RoleSerializer(serializers.ModelSerializer):
    user_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Role
        fields = [
            'id', 'name',
            'can_edit_duty_roster', 'can_schedule_meetings',
            'can_create_announcements', 'can_edit_announcements',
            'can_record_discipline', 'can_view_discipline',
            'can_add_clubs', 'can_manage_competitions',
            'user_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_user_count(self, obj):
        return obj.users.count()


class UserSerializer(serializers.ModelSerializer):
    role_detail = RoleSerializer(source='role', read_only=True)
    full_name = serializers.SerializerMethodField()
    is_c_suite = serializers.ReadOnlyField()
    is_captain = serializers.ReadOnlyField()
    is_class_rep = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'role', 'role_detail', 'phone', 'grade',
            'section', 'house', 'is_phase_head', 'avatar',
            'bio', 'is_active', 'is_staff', 'is_superuser', 'is_c_suite', 'is_captain',
            'is_class_rep', 'date_joined', 'created_at', 'updated_at'
        ]
        read_only_fields = ['date_joined', 'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone', 'grade', 'section', 'house'
        ]
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords do not match")
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSessionSerializer(serializers.ModelSerializer):
    user_detail = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = UserSession
        fields = ['id', 'user', 'user_detail', 'ip_address', 'user_agent', 'created_at', 'expires_at']
        read_only_fields = ['created_at']