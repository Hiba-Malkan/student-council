from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import DisciplineRecord
from .serializers import DisciplineRecordSerializer
from .permissions import IsDisciplineManager


class DisciplineRecordViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing discipline records.
    
    - List: GET /api/discipline/
    - Create: POST /api/discipline/
    - Retrieve: GET /api/discipline/{id}/
    - Update: PUT/PATCH /api/discipline/{id}/
    - Delete: DELETE /api/discipline/{id}/
    """
    queryset = DisciplineRecord.objects.all()
    serializer_class = DisciplineRecordSerializer
    permission_classes = [IsAuthenticated, IsDisciplineManager]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filter by fields
    filterset_fields = ['class_section', 'dno']
    
    # Search by student name or Dno
    search_fields = ['student_name', 'dno', 'class_section']
    
    # Allow ordering
    ordering_fields = ['student_name', 'class_section', 'offense_count', 'created_at']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        """
        Automatically set the created_by field to the current user
        """
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """
        Save updates
        """
        serializer.save()