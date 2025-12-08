from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from .models import Notification, NotificationPreference, EmailTemplate
from .serializers import NotificationSerializer, NotificationPreferenceSerializer, EmailTemplateSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """View and manage notifications"""
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['notification_type', 'is_read', 'is_snoozed']
    
    def get_queryset(self):
        user = self.request.user
        queryset = Notification.objects.filter(recipient=user)
        
        # Filter out snoozed notifications that are still snoozed
        now = timezone.now()
        queryset = queryset.exclude(
            is_snoozed=True,
            snoozed_until__gt=now
        )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread notifications"""
        notifications = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'count': count})
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        
        return Response(NotificationSerializer(notification).data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        updated = self.get_queryset().filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return Response({'marked_read': updated})
    
    @action(detail=True, methods=['post'])
    def snooze(self, request, pk=None):
        """Snooze notification"""
        notification = self.get_object()
        
        # Default snooze: 1 hour
        snooze_duration = request.data.get('duration_hours', 1)
        notification.is_snoozed = True
        notification.snoozed_until = timezone.now() + timedelta(hours=snooze_duration)
        notification.save()
        
        return Response(NotificationSerializer(notification).data)
    
    @action(detail=True, methods=['post'])
    def unsnooze(self, request, pk=None):
        """Unsnooze notification"""
        notification = self.get_object()
        notification.is_snoozed = False
        notification.snoozed_until = None
        notification.save()
        
        return Response(NotificationSerializer(notification).data)
    
    @action(detail=False, methods=['delete'])
    def clear_read(self, request):
        """Delete all read notifications"""
        deleted_count = self.get_queryset().filter(is_read=True).delete()[0]
        return Response({'deleted': deleted_count})


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    """Manage user notification preferences"""
    queryset = NotificationPreference.objects.all()
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def my_preferences(self, request):
        """Get or update current user's notification preferences"""
        preference, created = NotificationPreference.objects.get_or_create(
            user=request.user
        )
        
        if request.method in ['PUT', 'PATCH']:
            serializer = self.get_serializer(preference, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        
        serializer = self.get_serializer(preference)
        return Response(serializer.data)


class EmailTemplateViewSet(viewsets.ModelViewSet):
    """Manage email templates (C-Suite only)"""
    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if not self.request.user.is_c_suite:
            return EmailTemplate.objects.none()
        return EmailTemplate.objects.all()
    
    def create(self, request, *args, **kwargs):
        if not request.user.is_c_suite:
            return Response(
                {'error': 'Only C-Suite can create email templates'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        if not request.user.is_c_suite:
            return Response(
                {'error': 'Only C-Suite can update email templates'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        if not request.user.is_c_suite:
            return Response(
                {'error': 'Only C-Suite can delete email templates'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)