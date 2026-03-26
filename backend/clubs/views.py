from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.views.generic import TemplateView
from django.db.models import Sum

from .models import Club
from .serializers import (
    ClubListSerializer,
    ClubDetailSerializer,
    ClubCreateUpdateSerializer
)
from .permissions import CanManageClubs


class ClubViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing clubs.
    
    Permissions:
    - List/Retrieve: Any user (authenticated or anonymous)
    - Create/Update/Delete: Users with can_add_clubs permission
    """
    queryset = Club.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'established_by', 'tutors']
    filterset_fields = ['status']
    ordering_fields = ['name', 'established_year', 'member_count', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return ClubListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ClubCreateUpdateSerializer
        return ClubDetailSerializer
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'change_status']:
            permission_classes = [IsAuthenticated, CanManageClubs]
        else:
            # Allow any user (authenticated or anonymous) to view clubs
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """Set created_by when creating a club"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanManageClubs])
    def change_status(self, request, pk=None):
        """
        Change club status.
        
        POST /api/clubs/{id}/change_status/
        Body: {"status": "active"|"under_review"|"inactive"}
        """
        club = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Club.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status. Must be: active, under_review, or inactive'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        club.status = new_status
        club.save()
        
        serializer = ClubDetailSerializer(club, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get club statistics.
        
        GET /api/clubs/stats/
        Returns: {
            "total_clubs": int,
            "active_clubs": int,
            "under_review": int,
            "inactive_clubs": int,
            "total_members": int
        }
        """
        total_clubs = Club.objects.count()
        active_clubs = Club.objects.filter(status='active').count()
        under_review = Club.objects.filter(status='under_review').count()
        inactive_clubs = Club.objects.filter(status='inactive').count()
        total_members = Club.objects.aggregate(
            total=Sum('member_count')
        )['total'] or 0
        
        return Response({
            'total_clubs': total_clubs,
            'active_clubs': active_clubs,
            'under_review': under_review,
            'inactive_clubs': inactive_clubs,
            'total_members': total_members,
        })


# HTML Template Views

class ClubsOverviewView(TemplateView):
    """Display clubs overview page"""
    template_name = 'clubs/clubs.html'


class ClubFormView(TemplateView):
    """Display club create/edit form"""
    template_name = 'clubs/clubs_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # For edit mode, pass club_id to template
        context['club_id'] = self.kwargs.get('pk')
        return context