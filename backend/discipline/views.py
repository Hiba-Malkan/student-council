# discipline/views.py
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import DisciplineRecord, OffenseLog  # Added OffenseLog
from .serializers import DisciplineRecordSerializer
from .permissions import IsDisciplineManager


class DisciplineRecordViewSet(viewsets.ModelViewSet):
    queryset = DisciplineRecord.objects.all()
    serializer_class = DisciplineRecordSerializer
    permission_classes = [IsAuthenticated, IsDisciplineManager]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filter by fields (NEW: added category for filtering if needed via logs)
    filterset_fields = ['class_section', 'dno']
    
    # Search by student name or Dno
    search_fields = ['student_name', 'dno', 'class_section']
    
    # Allow ordering
    ordering_fields = ['student_name', 'class_section', 'offense_count', 'created_at']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        """
        Automatically set the created_by field to the current user
        and create initial offense log
        """
        instance = serializer.save(created_by=self.request.user)
        # NEW: Create initial offense log
        category = self.request.data.get('category', 'OTHER')
        reason = self.request.data.get('reason', '')
        OffenseLog.objects.create(
            record=instance,
            category=category,
            reason=reason
        )

    def perform_update(self, serializer):
        """
        Save updates and add new log if offense_count increased
        """
        instance = serializer.instance
        old_count = instance.offense_count
        instance = serializer.save()
        
        # NEW: If count increased, add new log
        if instance.offense_count > old_count:
            category = self.request.data.get('category', 'OTHER')
            reason = self.request.data.get('reason', '')
            OffenseLog.objects.create(
                record=instance,
                category=category,
                reason=reason
            )