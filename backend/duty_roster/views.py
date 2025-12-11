from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db import models
from datetime import datetime, timedelta
from .models import Duty, DutyType  
from .serializers import DutySerializer, DutyTypeSerializer 


class DutyTypeViewSet(viewsets.ModelViewSet):
    """CRUD operations for duty types (C-Suite only)"""
    queryset = DutyType.objects.all()
    serializer_class = DutyTypeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description', 'location']
    
    def create(self, request, *args, **kwargs):
        if not request.user.is_c_suite:
            return Response(
                {'error': 'Only C-Suite can create duty types'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        if not request.user.is_c_suite:
            return Response(
                {'error': 'Only C-Suite can update duty types'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        if not request.user.is_c_suite:
            return Response(
                {'error': 'Only C-Suite can delete duty types'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


class DutyViewSet(viewsets.ModelViewSet):
    """CRUD operations for duties"""
    queryset = Duty.objects.select_related('assigned_to', 'assigned_by')
    serializer_class = DutySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['date', 'assigned_to', 'is_completed', 'duty_type']
    filter_backends = [filters.SearchFilter]
    search_fields = ['duty_type_name', 'location', 'subsidiary_area', 'instructions',
                     'assigned_to__username', 'assigned_to__first_name', 'assigned_to__last_name']
    
    def get_queryset(self):
        queryset = Duty.objects.select_related('assigned_to', 'assigned_by')
        
        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        # Filter by assigned_to if explicitly provided in query params
        assigned_to_id = self.request.query_params.get('assigned_to')
        if assigned_to_id:
            queryset = queryset.filter(assigned_to_id=assigned_to_id)
            return queryset.order_by('-date', '-created_at')
        
        # Role-based filtering (only if assigned_to not explicitly specified)
        # Show all duties if user is staff, superuser, c-suite, captain, or has duty roster permission
        can_see_all = (
            self.request.user.is_staff or 
            self.request.user.is_superuser or
            self.request.user.is_c_suite or 
            self.request.user.is_captain or
            (self.request.user.role and self.request.user.role.can_edit_duty_roster)
        )
        
        if not can_see_all:
            # Regular users only see their own duties
            queryset = queryset.filter(assigned_to=self.request.user)
        
        return queryset.order_by('-date', '-created_at')
    
    def create(self, request, *args, **kwargs):
        # Check permissions - staff, superuser, or role with permission
        if not (request.user.is_staff or request.user.is_superuser or 
                (request.user.role and request.user.role.can_edit_duty_roster)):
            return Response(
                {'error': 'You do not have permission to create duties'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create a mutable copy of request data
        data = request.data.copy()
        
        # Validate required fields
        if not data.get('duty_type_name'):
            return Response(
                {'error': 'duty_type_name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer):
        """Override to set assigned_by"""
        serializer.save(assigned_by=self.request.user)
    
    def update(self, request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser or 
                (request.user.role and request.user.role.can_edit_duty_roster)):
            return Response(
                {'error': 'You do not have permission to update duties'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser or 
                (request.user.role and request.user.role.can_edit_duty_roster)):
            return Response(
                {'error': 'You do not have permission to delete duties'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def my_duty(self, request):
        """Get current user's duty for today and upcoming"""
        today = timezone.now().date()
        
        # Today's duty
        today_duty = Duty.objects.filter(
            assigned_to=request.user,
            date=today
        ).first()
        
        # Next upcoming duty
        next_duty = Duty.objects.filter(
            assigned_to=request.user,
            date__gt=today
        ).order_by('date').first()
        
        return Response({
            'today': DutySerializer(today_duty).data if today_duty else None,
            'next': DutySerializer(next_duty).data if next_duty else None,
        })
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get all duties for today"""
        today = timezone.now().date()
        duties = Duty.objects.filter(date=today)
        serializer = self.get_serializer(duties, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_complete(self, request, pk=None):
        """Mark duty as completed"""
        duty = self.get_object()
        
        if duty.assigned_to != request.user and not request.user.is_c_suite:
            return Response(
                {'error': 'You can only mark your own duties as complete'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        duty.is_completed = True
        duty.completed_at = timezone.now()
        duty.notes = request.data.get('notes', '')
        duty.save()
        
        return Response(DutySerializer(duty).data)
