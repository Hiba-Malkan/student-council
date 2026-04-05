from rest_framework import serializers
from .models import User, Role, UserSession, PasswordResetOTP, ContactMessage


class RoleSerializer(serializers.ModelSerializer):
    user_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Role
        fields = [
            'id', 'name', 'is_normal_student',
            'can_edit_duty_roster', 'can_schedule_meetings',
            'can_create_announcements', 'can_edit_announcements',
            'can_record_discipline', 'can_view_discipline',
            'can_add_clubs', 'can_manage_competitions', 'can_manage_gatepass',
            'user_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_user_count(self, obj):
        return obj.users.count()


class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    is_c_suite = serializers.ReadOnlyField()
    is_captain = serializers.ReadOnlyField()
    is_class_rep = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'role', 'phone', 'grade',
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


class ForgotPasswordSerializer(serializers.Serializer):
    """Serializer for initiating password reset - accepts email or username"""
    identifier = serializers.CharField(
        help_text="Email address or username"
    )
    
    def validate(self, data):
        """Find and validate the user"""
        identifier = data.get('identifier')
        user = None
        
        if '@' in identifier:
            # It's an email
            try:
                user = User.objects.get(email=identifier, is_active=True)
            except User.DoesNotExist:
                raise serializers.ValidationError("No account found with this email address.")
        else:
            # It's a username
            try:
                user = User.objects.get(username=identifier, is_active=True)
            except User.DoesNotExist:
                raise serializers.ValidationError("No account found with this username.")
        
        if not user.email:
            raise serializers.ValidationError("This account does not have an email address set.")
        
        # Add user to validated data
        data['user'] = user
        return data


class VerifyOTPSerializer(serializers.Serializer):
    """Serializer for verifying OTP"""
    identifier = serializers.CharField(
        help_text="Email address or username"
    )
    otp = serializers.CharField(
        min_length=6,
        max_length=6,
        help_text="6-digit OTP code"
    )
    
    def validate_otp(self, value):
        """Validate OTP format"""
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only digits.")
        return value


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for resetting password with OTP"""
    identifier = serializers.CharField(
        help_text="Email address or username"
    )
    otp = serializers.CharField(
        min_length=6,
        max_length=6,
        help_text="6-digit OTP code"
    )
    new_password = serializers.CharField(
        min_length=8,
        write_only=True,
        help_text="New password (minimum 8 characters)"
    )
    confirm_password = serializers.CharField(
        write_only=True,
        help_text="Confirm new password"
    )
    
    def validate_otp(self, value):
        """Validate OTP format"""
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only digits.")
        return value
    
    def validate(self, data):
        """Validate passwords match"""
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match."
            })
        return data


class ContactMessageSerializer(serializers.ModelSerializer):
    """Serializer for contact admin messages"""
    responded_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ContactMessage
        fields = [
            'id', 'name', 'email', 'username', 'subject', 'message',
            'status', 'admin_response', 'responded_by', 'responded_by_name',
            'responded_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['status', 'admin_response', 'responded_by', 'responded_at', 'created_at', 'updated_at']
    
    def get_responded_by_name(self, obj):
        if obj.responded_by:
            return obj.responded_by.get_full_name() or obj.responded_by.username
        return None
    
    def validate_email(self, value):
        """Validate email format"""
        if not value:
            raise serializers.ValidationError("Email is required.")
        return value.lower()
    
    def validate_message(self, value):
        """Ensure message is not too short"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Message must be at least 10 characters long.")
        return value
