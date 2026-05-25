from rest_framework import serializers
from .models import DisciplineRecord, OffenseLog  


class OffenseLogSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = OffenseLog
        fields = ['id', 'category', 'category_display', 'reason', 'created_at']
        read_only_fields = ['created_at']
    
    def validate_category(self, value):
        valid_choices = [choice[0] for choice in OffenseLog.CATEGORY_CHOICES]
        if value not in valid_choices:
            raise serializers.ValidationError(f"Invalid category. Must be one of: {', '.join(valid_choices)}")
        return value


class DisciplineRecordSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField(read_only=True)
    category = serializers.CharField(write_only=True, required=False, allow_blank=True)
    reason = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    def get_created_by_name(self, obj):
        if obj.created_by:
            full_name = obj.created_by.get_full_name()
            return full_name if full_name else obj.created_by.username
        return 'Unknown'

    offense_logs = OffenseLogSerializer(many=True, read_only=True)
    latest_category = serializers.SerializerMethodField()
    last_offense_date = serializers.SerializerMethodField()

    def get_latest_category(self, obj):
        log = obj.offense_logs.first()
        return log.get_category_display() if log else "—"

    def get_last_offense_date(self, obj):
        log = obj.offense_logs.first()
        return log.created_at if log else None

    class Meta:
        model = DisciplineRecord
        fields = [
            'id',
            'student_name',
            'class_section',
            'dno',
            'offense_count',
            'created_by',
            'created_by_name',
            'created_at',
            'updated_at',
            'offense_logs',        
            'latest_category',     
            'last_offense_date',
            'category',
            'reason',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance is not None:
            for field_name, field in self.fields.items():
                if field_name not in self.Meta.read_only_fields:
                    field.required = False

    def create(self, validated_data):
        validated_data.pop('category', None)
        validated_data.pop('reason', None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('category', None)
        validated_data.pop('reason', None)
        return super().update(instance, validated_data)

    def validate_dno(self, value):
        if not value:
            return value
            
        value = value.upper()
        if not value.startswith('D'):
            raise serializers.ValidationError("Dno must start with 'D'")
        if len(value) < 5 or len(value) > 9:
            raise serializers.ValidationError("Dno must be 5-9 characters (D + 4-8 digits)")
        if not value[1:].isdigit():
            raise serializers.ValidationError("Only digits allowed after 'D'")
        
        if self.instance and self.instance.dno == value:
            return value
        
        if DisciplineRecord.objects.filter(dno=value).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError("A record with this D.No already exists")
        
        return value

    def validate_offense_count(self, value):
        if value < 1:
            raise serializers.ValidationError("Offense count must be at least 1")
        return value