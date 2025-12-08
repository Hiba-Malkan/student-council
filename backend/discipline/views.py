from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Q
from datetime import date, timedelta
from .models import DisciplineOffence, OffenceType, DefaulterReport, DisciplineAction
from .serializers import (
    DisciplineOffenceSerializer, OffenceTypeSerializer,
    DefaulterReportSerializer, DisciplineActionSerializer
)


class OffenceTypeViewSet(viewsets.ModelViewSet):
    """CRUD operations for offence types (C-Suite only)"""
    queryset = OffenceType.objects.all()
    serializer_class = OffenceTypeSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        if not request.user.is_c_suite:
            return Response(
                {'error': 'Only C-Suite can create offence types'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        if not request.user.is_c_suite:
            return Response(
                {'error': 'Only C-Suite can update offence types'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        if not request.user.is_c_suite:
            return Response(
                {'error': 'Only C-Suite can delete offence types'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


class DisciplineOffenceViewSet(viewsets.ModelViewSet):
    """CRUD operations for discipline offences"""
    queryset = DisciplineOffence.objects.select_related('student', 'offence_type', 'recorded_by', 'reviewed_by')
    serializer_class = DisciplineOffenceSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['student', 'offence_type', 'date', 'status']
    search_fields = ['student__username', 'student__first_name', 'student__last_name', 'description']
    
    def get_queryset(self):
        user = self.request.user
        queryset = DisciplineOffence.objects.select_related('student', 'offence_type', 'recorded_by', 'reviewed_by')
        
        # Class reps can only see offences they recorded
        if user.is_class_rep and not (user.is_c_suite or user.is_phase_head):
            queryset = queryset.filter(recorded_by=user)
        
        # Phase heads see offences for their phase
        elif user.is_phase_head and not user.is_c_suite:
            queryset = queryset.filter(student__phase=user.phase)
        
        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        if not request.user.role.can_record_discipline:
            return Response(
                {'error': 'You do not have permission to record discipline offences'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        request.data['recorded_by'] = request.user.id
        request.data['date'] = request.data.get('date', timezone.now().date())
        
        return super().create(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        offence = serializer.save()
        
        # Check if student has reached threshold (3 offences in last 30 days)
        recent_offences = DisciplineOffence.objects.filter(
            student=offence.student,
            date__gte=timezone.now().date() - timedelta(days=30)
        ).count()
        
        if recent_offences >= 3:
            # TODO: Trigger defaulter report generation (via Celery)
            pass
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get all offences recorded today"""
        today = timezone.now().date()
        offences = self.get_queryset().filter(date=today)
        serializer = self.get_serializer(offences, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending offences for review"""
        if not (request.user.is_phase_head or request.user.is_c_suite):
            return Response(
                {'error': 'Only phase heads can view pending offences'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        offences = self.get_queryset().filter(status='PENDING')
        serializer = self.get_serializer(offences, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """Review an offence (Phase heads)"""
        if not (request.user.is_phase_head or request.user.is_c_suite):
            return Response(
                {'error': 'Only phase heads can review offences'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        offence = self.get_object()
        offence.status = request.data.get('status', 'REVIEWED')
        offence.reviewed_by = request.user
        offence.reviewed_at = timezone.now()
        offence.review_notes = request.data.get('notes', '')
        offence.save()
        
        return Response(DisciplineOffenceSerializer(offence).data)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve an offence (Phase heads)"""
        if not (request.user.is_phase_head or request.user.is_c_suite):
            return Response(
                {'error': 'Only phase heads can resolve offences'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        offence = self.get_object()
        offence.status = 'RESOLVED'
        offence.action_taken = request.data.get('action_taken', '')
        offence.parent_notified = request.data.get('parent_notified', False)
        if offence.parent_notified:
            offence.parent_notification_date = timezone.now().date()
        offence.save()
        
        return Response(DisciplineOffenceSerializer(offence).data)
    
    @action(detail=True, methods=['post'])
    def escalate(self, request, pk=None):
        """Escalate an offence (Phase heads)"""
        if not (request.user.is_phase_head or request.user.is_c_suite):
            return Response(
                {'error': 'Only phase heads can escalate offences'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        offence = self.get_object()
        offence.status = 'ESCALATED'
        offence.review_notes = request.data.get('notes', '')
        offence.save()
        
        return Response(DisciplineOffenceSerializer(offence).data)
    
    @action(detail=False, methods=['get'])
    def defaulters(self, request):
        """Get list of students with 3+ offences"""
        if not (request.user.is_phase_head or request.user.is_c_suite):
            return Response(
                {'error': 'Only phase heads can view defaulters'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get students with 3+ offences in last 30 days
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        
        defaulters = DisciplineOffence.objects.filter(
            date__gte=thirty_days_ago
        ).values('student').annotate(
            offence_count=Count('id')
        ).filter(offence_count__gte=3)
        
        # If phase head, filter by their phase
        if request.user.is_phase_head and not request.user.is_c_suite:
            defaulters = defaulters.filter(student__phase=request.user.phase)
        
        return Response(defaulters)


class DefaulterReportViewSet(viewsets.ReadOnlyModelViewSet):
    """View defaulter reports"""
    queryset = DefaulterReport.objects.prefetch_related('defaulters')
    serializer_class = DefaulterReportSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['date', 'phase']
    
    def get_queryset(self):
        user = self.request.user
        queryset = DefaulterReport.objects.prefetch_related('defaulters')
        
        # Phase heads see only their phase's reports
        if user.is_phase_head and not user.is_c_suite:
            queryset = queryset.filter(phase=user.phase)
        elif not (user.is_phase_head or user.is_c_suite):
            return DefaulterReport.objects.none()
        
        return queryset


class DisciplineActionViewSet(viewsets.ModelViewSet):
    """Manage discipline actions"""
    queryset = DisciplineAction.objects.select_related('offence', 'assigned_by')
    serializer_class = DisciplineActionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['offence', 'action_type', 'is_completed']
    
    def get_queryset(self):
        user = self.request.user
        
        if not (user.is_phase_head or user.is_c_suite):
            return DisciplineAction.objects.none()
        
        queryset = DisciplineAction.objects.select_related('offence', 'assigned_by')
        
        # Phase heads see actions for their phase
        if user.is_phase_head and not user.is_c_suite:
            queryset = queryset.filter(offence__student__phase=user.phase)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        if not (request.user.is_phase_head or request.user.is_c_suite):
            return Response(
                {'error': 'Only phase heads can create discipline actions'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        request.data['assigned_by'] = request.user.id
        return super().create(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def mark_complete(self, request, pk=None):
        """Mark action as completed"""
        if not (request.user.is_phase_head or request.user.is_c_suite):
            return Response(
                {'error': 'Only phase heads can mark actions as complete'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        action = self.get_object()
        action.is_completed = True
        action.date_completed = timezone.now().date()
        action.save()
        
        return Response(DisciplineActionSerializer(action).data)