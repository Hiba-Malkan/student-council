from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend

from .models import Feedback
from .serializers import (
    FeedbackListSerializer,
    FeedbackDetailSerializer,
    FeedbackCreateSerializer
)
from .permissions import CanManageFeedback


class FeedbackViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing feedback and issue reports.
    
    Provides endpoints for:
    - Creating feedback (public)
    - Viewing feedback (authenticated users can see their own, staff can see all)
    - Managing feedback (staff/managers only)
    """
    
    queryset = Feedback.objects.all()
    permission_classes = [CanManageFeedback]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['subject', 'description', 'name', 'email', 'category']
    filterset_fields = ['type', 'status', 'priority', 'category']
    ordering_fields = ['created_at', 'priority', 'status']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return FeedbackCreateSerializer
        elif self.action == 'list':
            return FeedbackListSerializer
        return FeedbackDetailSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Only staff/superusers and managers can view feedback list
        if not (self.request.user.is_staff or self.request.user.is_superuser):
            if hasattr(self.request.user, 'role') and self.request.user.role:
                if not getattr(self.request.user.role, 'can_manage_feedback', False):
                    # Normal users don't get any feedback in the list
                    return queryset.none()
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Create new feedback - allow anonymous or authenticated users"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response({
            'success': True,
            'message': 'Thank you for your feedback! We appreciate your input and will review it shortly.',
            'id': serializer.instance.id
        }, status=status.HTTP_201_CREATED)
    
    def perform_create(self, serializer):
        """Set submitted_by if user is authenticated"""
        if self.request.user.is_authenticated:
            serializer.save(submitted_by=self.request.user)
        else:
            serializer.save()
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def assign(self, request, pk=None):
        """Assign feedback to a staff member"""
        feedback = self.get_object()
        
        # Check if user has permission
        if not (request.user.is_staff or request.user.is_superuser):
            if hasattr(request.user, 'role') and request.user.role:
                if not getattr(request.user.role, 'can_manage_feedback', False):
                    return Response(
                        {'error': 'You do not have permission to assign feedback'},
                        status=status.HTTP_403_FORBIDDEN
                    )
        
        assigned_to_id = request.data.get('assigned_to_id')
        if not assigned_to_id:
            return Response(
                {'error': 'assigned_to_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from django.contrib.auth.models import User
        try:
            assigned_user = User.objects.get(id=assigned_to_id, is_staff=True)
            feedback.assigned_to = assigned_user
            feedback.save()
            return Response({
                'success': True,
                'message': f'Feedback assigned to {assigned_user.get_full_name() or assigned_user.username}'
            })
        except User.DoesNotExist:
            return Response(
                {'error': 'Staff member not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def update_status(self, request, pk=None):
        """Update feedback status"""
        feedback = self.get_object()
        
        # Check if user has permission
        if not (request.user.is_staff or request.user.is_superuser):
            if hasattr(request.user, 'role') and request.user.role:
                if not getattr(request.user.role, 'can_manage_feedback', False):
                    return Response(
                        {'error': 'You do not have permission to update feedback status'},
                        status=status.HTTP_403_FORBIDDEN
                    )
        
        new_status = request.data.get('status')
        if not new_status or new_status not in dict(Feedback.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status. Valid options: OPEN, IN_PROGRESS, RESOLVED, CLOSED'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        feedback.status = new_status
        if new_status == 'RESOLVED':
            from django.utils import timezone
            feedback.resolved_at = timezone.now()
        feedback.save()
        
        return Response({
            'success': True,
            'message': f'Feedback status updated to {feedback.get_status_display()}',
            'status': new_status
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def add_notes(self, request, pk=None):
        """Add admin notes to feedback"""
        feedback = self.get_object()
        
        # Check if user has permission
        if not (request.user.is_staff or request.user.is_superuser):
            if hasattr(request.user, 'role') and request.user.role:
                if not getattr(request.user.role, 'can_manage_feedback', False):
                    return Response(
                        {'error': 'You do not have permission to add notes'},
                        status=status.HTTP_403_FORBIDDEN
                    )
        
        notes = request.data.get('notes', '').strip()
        if not notes:
            return Response(
                {'error': 'Notes cannot be empty'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Append to existing notes
        if feedback.admin_notes:
            feedback.admin_notes += f"\n\n[{request.user.get_full_name() or request.user.username}]: {notes}"
        else:
            feedback.admin_notes = f"[{request.user.get_full_name() or request.user.username}]: {notes}"
        
        feedback.save()
        
        return Response({
            'success': True,
            'message': 'Note added successfully',
            'admin_notes': feedback.admin_notes
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def update_priority(self, request, pk=None):
        """Update feedback priority"""
        feedback = self.get_object()
        
        # Check if user has permission
        if not (request.user.is_staff or request.user.is_superuser):
            if hasattr(request.user, 'role') and request.user.role:
                if not getattr(request.user.role, 'can_manage_feedback', False):
                    return Response(
                        {'error': 'You do not have permission to update feedback priority'},
                        status=status.HTTP_403_FORBIDDEN
                    )
        
        new_priority = request.data.get('priority')
        if not new_priority or new_priority not in dict(Feedback.PRIORITY_CHOICES):
            return Response(
                {'error': 'Invalid priority. Valid options: LOW, MEDIUM, HIGH, CRITICAL'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        feedback.priority = new_priority
        feedback.save()
        
        return Response({
            'success': True,
            'message': f'Feedback priority updated to {feedback.get_priority_display()}',
            'priority': new_priority
        })
