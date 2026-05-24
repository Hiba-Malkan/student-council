from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db import models
from datetime import datetime, timedelta
from .models import Duty, DutyType  
from .serializers import DutySerializer, DutyTypeSerializer
from accounts.models import User


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
    
    def _can_edit(self, user):
        return (
            user.is_staff or
            user.is_superuser or
            user.is_c_suite or
            user.is_captain or
            (user.role and user.role.can_edit_duty_roster)
        )

    def get_queryset(self):
        queryset = Duty.objects.select_related('assigned_to', 'assigned_by')
        
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        assigned_to_id = self.request.query_params.get('assigned_to')
        if assigned_to_id:
            queryset = queryset.filter(assigned_to_id=assigned_to_id)
            return queryset.order_by('-date', '-created_at')
        
        if not self._can_edit(self.request.user):
            queryset = queryset.filter(assigned_to=self.request.user)
        
        return queryset.order_by('-date', '-created_at')
    
    def create(self, request, *args, **kwargs):
        if not self._can_edit(request.user):
            return Response(
                {'error': 'You do not have permission to create duties'},
                status=status.HTTP_403_FORBIDDEN
            )

        data = request.data.copy()
        user_id = data.get('assigned_to')

        # --- Enforce duty roster visibility ---
        if user_id:
            try:
                assignee = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response(
                    {'error': 'Assigned user not found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not assignee.is_visible_in_duty_roster:
                return Response(
                    {'error': f'{assignee.get_full_name() or assignee.username} is not eligible to be assigned duties.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        date_str = data.get('date')
        if user_id and date_str:
            user_id_int = int(user_id)
            duty_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            month_start = duty_date.replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1)
            if not Duty.objects.filter(assigned_to_id=user_id_int, date__gte=month_start, date__lt=month_end).exists():
                duty_types = list(DutyType.objects.all())
                if duty_types:
                    last_month = (month_start - timedelta(days=1)).replace(day=1)
                    last_duty = Duty.objects.filter(assigned_to_id=user_id_int, date__gte=last_month, date__lt=month_start).order_by('date').first()
                    if last_duty and last_duty.duty_type in duty_types:
                        idx = duty_types.index(last_duty.duty_type)
                        next_idx = (idx + 1) % len(duty_types)
                    else:
                        next_idx = 0
                    next_duty_type = duty_types[next_idx]
                    data['duty_type'] = next_duty_type.id
                    data['duty_type_name'] = next_duty_type.name
                    data['location'] = data.get('location') or next_duty_type.location

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
        serializer.save(assigned_by=self.request.user)
    
    def update(self, request, *args, **kwargs):
        if not self._can_edit(request.user):
            return Response(
                {'error': 'You do not have permission to update duties'},
                status=status.HTTP_403_FORBIDDEN
            )
        # If assigned_to is being changed, enforce visibility on the new assignee too
        new_assignee_id = request.data.get('assigned_to')
        if new_assignee_id:
            try:
                assignee = User.objects.get(id=new_assignee_id)
            except User.DoesNotExist:
                return Response(
                    {'error': 'Assigned user not found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not assignee.is_visible_in_duty_roster:
                return Response(
                    {'error': f'{assignee.get_full_name() or assignee.username} is not eligible to be assigned duties.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        if not self._can_edit(request.user):
            return Response(
                {'error': 'You do not have permission to delete duties'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def my_duty(self, request):
        today = timezone.now().date()
        today_duty = Duty.objects.filter(assigned_to=request.user, date=today).first()
        next_duty = Duty.objects.filter(assigned_to=request.user, date__gt=today).order_by('date').first()
        return Response({
            'today': DutySerializer(today_duty).data if today_duty else None,
            'next': DutySerializer(next_duty).data if next_duty else None,
        })
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        today = timezone.now().date()
        duties = Duty.objects.filter(date=today)
        serializer = self.get_serializer(duties, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_complete(self, request, pk=None):
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