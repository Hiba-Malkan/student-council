from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny
from rest_framework import status

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
    
    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def signup(self, request, pk=None):
        """
        Public endpoint for students to sign up for a competition.
        
        POST /api/competitions/{id}/signup/
        Body: {
            "participant_name": "string",
            "email": "string",
            "phone": "string (optional)",
            "team_name": "string (optional)",
            "message": "string (optional)"
        }
        
        No authentication required - open to public.
        """
        competition = self.get_object()
        
        # Validate required fields
        participant_name = request.data.get('participant_name', '').strip()
        email = request.data.get('email', '').strip()
        
        if not participant_name:
            return Response(
                {'error': 'Participant name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not email:
            return Response(
                {'error': 'Email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Basic email validation
        if '@' not in email:
            return Response(
                {'error': 'Invalid email format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if competition is active
        if not competition.is_active:
            return Response(
                {'error': 'This competition is not currently open for signups'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'success': True,
            'message': f'Thank you {participant_name}! Your signup for {competition.name} has been received. You will be contacted soon with further details.',
            'competition_id': competition.id,
            'competition_name': competition.name
        }, status=status.HTTP_201_CREATED)
