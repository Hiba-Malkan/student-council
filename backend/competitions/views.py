from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status

from .models import Competition, CompetitionSignup
from .serializers import (
    CompetitionSerializer,
    CompetitionListSerializer,
    CompetitionSignupSerializer
)
from .permissions import CanManageCompetitions, CanViewCompetitionSignups


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
            "student_name": "string",
            "email": "string",
            "phone": "string (optional)",
            "team_name": "string (optional)",
            "message": "string (optional)"
        }
        
        No authentication required - open to public.
        """
        competition = self.get_object()
        
        # Validate required fields
        student_name = request.data.get('student_name', '').strip()
        email = request.data.get('email', '').strip()
        
        if not student_name:
            return Response(
                {'error': 'Student name is required'},
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
        
        # Save signup to database
        try:
            signup, created = CompetitionSignup.objects.update_or_create(
                competition=competition,
                email=email,
                defaults={
                    'student_name': student_name,
                    'phone': request.data.get('phone', ''),
                    'team_name': request.data.get('team_name', ''),
                    'message': request.data.get('message', ''),
                }
            )
            
            action_msg = 'registered' if created else 'updated your registration for'
            return Response({
                'success': True,
                'message': f'Thank you {student_name}! You have {action_msg} {competition.name}. You will be contacted soon with further details.',
                'competition_id': competition.id,
                'competition_name': competition.name
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': f'Failed to process signup: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'], permission_classes=[CanViewCompetitionSignups])
    def signups(self, request, pk=None):
        """
        Get all signups for a competition.
        
        GET /api/competitions/{id}/signups/
        Requires: CanViewCompetitionSignups permission (can_manage_competitions role)
        """
        competition = self.get_object()
        signups = competition.signups.all()
        serializer = CompetitionSignupSerializer(signups, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['delete'], permission_classes=[CanViewCompetitionSignups])
    def delete_signup(self, request, pk=None):
        """
        Delete a signup from a competition.
        
        DELETE /api/competitions/{id}/delete_signup/?signup_id={signup_id}
        Requires: CanViewCompetitionSignups permission (can_manage_competitions role)
        """
        competition = self.get_object()
        signup_id = request.query_params.get('signup_id')
        
        if not signup_id:
            return Response(
                {'error': 'signup_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            signup = CompetitionSignup.objects.get(id=signup_id, competition=competition)
            student_name = signup.student_name
            signup.delete()
            return Response({
                'success': True,
                'message': f'Signup from {student_name} has been deleted.'
            })
        except CompetitionSignup.DoesNotExist:
            return Response(
                {'error': 'Signup not found'},
                status=status.HTTP_404_NOT_FOUND
            )


# HTML Template Views
from django.views.generic import TemplateView


class CompetitionSignupsView(TemplateView):
    """Display competition signups management page"""
    template_name = 'competitions/competition-signups.html'
