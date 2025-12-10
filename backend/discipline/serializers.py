from rest_framework import serializers
from .models import DisciplineRecord


class DisciplineRecordSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
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
            'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def validate_dno(self, value):
        """
        Ensure Dno is in correct format
        """
        value = value.upper()
        if not value.startswith('D'):
            raise serializers.ValidationError("Dno must start with 'D'")
        if len(value) < 5 or len(value) > 9:
            raise serializers.ValidationError("Dno must be 5-9 characters (D followed by 4-8 digits)")
        if not value[1:].isdigit():
            raise serializers.ValidationError("Dno must contain only digits after 'D'")
        return value

    def validate_offense_count(self, value):
        """
        Ensure offense count is positive
        """
        if value < 1:
            raise serializers.ValidationError("Offense count must be at least 1")
        return value