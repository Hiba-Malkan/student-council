from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Competition
from .serializers import (
    CompetitionSerializer,
    CompetitionListSerializer
)
from .permissions import CanManageCompetitions


class CompetitionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing competitions.
    
    Provides CRUD operations for competitions.
    """
    queryset = Competition.objects.all()
    permission_classes = [CanManageCompetitions]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'hosted_by', 'participants', 'additional_info']
    filterset_fields = ['is_active']
    ordering_fields = ['created_at', 'event_date', 'name', 'participant_count']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CompetitionListSerializer
        return CompetitionSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            queryset = queryset.filter(event_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(event_date__lte=end_date)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get competition statistics.
        
        GET /api/competitions/stats/
        Returns: {
            "total_competitions": int,
            "active_competitions": int,
            "inactive_competitions": int,
            "total_participants": int
        }
        """
        total_competitions = Competition.objects.count()
        active_competitions = Competition.objects.filter(is_active=True).count()
        inactive_competitions = Competition.objects.filter(is_active=False).count()
        total_participants = sum([
            len(c.participants_list) 
            for c in Competition.objects.all()
        ])
        
        return Response({
            'total_competitions': total_competitions,
            'active_competitions': active_competitions,
            'inactive_competitions': inactive_competitions,
            'total_participants': total_participants,
        })
