from rest_framework import serializers
from .models import DisciplineRecord, OffenseLog  


class OffenseLogSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = OffenseLog
        fields = ['id', 'category', 'category_display', 'reason', 'created_at']
        read_only_fields = ['created_at']


class DisciplineRecordSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    # Full history 
    offense_logs = OffenseLogSerializer(many=True, read_only=True)

    # show latest category and date
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
        ]
        read_only_fields = ['id', 'offense_count', 'created_by', 'created_at', 'updated_at']

    def validate_dno(self, value):
        value = value.upper()
        if not value.startswith('D'):
            raise serializers.ValidationError("Dno must start with 'D'")
        if len(value) < 5 or len(value) > 9:
            raise serializers.ValidationError("Dno must be 5-9 characters (D + 4-8 digits)")
        if not value[1:].isdigit():
            raise serializers.ValidationError("Only digits allowed after 'D'")
        return value

    def validate_offense_count(self, value):
        if value < 1:
            raise serializers.ValidationError("Offense count must be at least 1")
        return value