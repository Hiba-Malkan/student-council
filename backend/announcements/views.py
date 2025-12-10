from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.utils import timezone
from django.db.models import Q
from .models import Announcement, EventParticipant, AnnouncementRead
from .serializers import AnnouncementSerializer, EventParticipantSerializer, AnnouncementReadSerializer


class AnnouncementViewSet(viewsets.ModelViewSet):
    """CRUD operations for announcements"""
    queryset = Announcement.objects.prefetch_related('target_roles', 'target_users')
    serializer_class = AnnouncementSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filterset_fields = ['announcement_type', 'is_published', 'is_pinned']
    search_fields = ['title', 'content']
    
    def get_queryset(self):
        user = self.request.user
        queryset = Announcement.objects.prefetch_related('target_roles', 'target_users')
        
        # Filter by announcement type if provided
        announcement_type = self.request.query_params.get('type')
        if announcement_type:
            queryset = queryset.filter(announcement_type=announcement_type)
        
        # Users see announcements targeted to them
        if not user.is_c_suite:
            queryset = queryset.filter(
                Q(is_public=True) |
                Q(target_roles=user.role) |
                Q(target_users=user) |
                Q(target_houses__contains=user.house) |
                Q(target_grades__contains=user.grade)
            ).distinct()
        
        return queryset.filter(is_published=True)
    
    def retrieve(self, request, *args, **kwargs):
        """Get single announcement with proper permissions"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={'request': request})
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        if not (request.user.is_superuser or (request.user.role and request.user.role.can_create_announcements)):
            return Response(
                {'error': 'You do not have permission to create announcements'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Handle both JSON and form data
        data = request.data.copy()
        
        # Set created_by to current user
        data['created_by'] = request.user.id
        
        # Set published_at if is_published is True
        is_published = data.get('is_published', 'true')
        if isinstance(is_published, str):
            is_published = is_published.lower() == 'true'
        
        if is_published:
            data['published_at'] = timezone.now()
        
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        announcement = self.get_object()
        
        # Superuser, C-Suite, or announcement creator with edit permissions can update
        if not (request.user.is_superuser or 
                request.user.is_c_suite or 
                (request.user.role and request.user.role.can_edit_announcements and announcement.created_by == request.user)):
            return Response(
                {'error': 'You do not have permission to update this announcement'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        if not (request.user.is_superuser or request.user.is_c_suite):
            return Response(
                {'error': 'Only superuser or C-Suite can delete announcements'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread announcements for current user"""
        read_ids = AnnouncementRead.objects.filter(user=request.user).values_list('announcement_id', flat=True)
        unread = self.get_queryset().exclude(id__in=read_ids)
        serializer = self.get_serializer(unread, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark announcement as read"""
        announcement = self.get_object()
        AnnouncementRead.objects.get_or_create(
            announcement=announcement,
            user=request.user
        )
        return Response({'status': 'marked as read'})
    
    @action(detail=True, methods=['post'])
    def pin(self, request, pk=None):
        """Pin/unpin announcement (Superuser or C-Suite only)"""
        if not (request.user.is_superuser or request.user.is_c_suite):
            return Response(
                {'error': 'Only superuser or C-Suite can pin announcements'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        announcement = self.get_object()
        announcement.is_pinned = not announcement.is_pinned
        announcement.save()
        
        return Response(AnnouncementSerializer(announcement, context={'request': request}).data)


class EventParticipantViewSet(viewsets.ModelViewSet):
    """Manage event participation"""
    queryset = EventParticipant.objects.select_related('announcement', 'user', 'assigned_by')
    serializer_class = EventParticipantSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['announcement', 'user', 'status']
    
    def get_queryset(self):
        user = self.request.user
        queryset = EventParticipant.objects.select_related('announcement', 'user', 'assigned_by')
        
        # Users can see their own participations
        # Captains can see participations for their events
        # C-Suite can see all
        if not (user.is_c_suite or user.is_captain):
            queryset = queryset.filter(user=user)
        
        announcement_id = self.request.query_params.get('announcement')
        if announcement_id:
            queryset = queryset.filter(announcement_id=announcement_id)
        
        user_id = self.request.query_params.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Register for an event"""
        # Users can register themselves, captains can assign others
        if 'user' not in request.data or request.data['user'] == request.user.id:
            request.data['user'] = request.user.id
        elif not request.user.role.can_manage_events:
            return Response(
                {'error': 'You do not have permission to assign participants'},
                status=status.HTTP_403_FORBIDDEN
            )
        else:
            request.data['assigned_by'] = request.user.id
        
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        participant = self.get_object()
        
        # Users can update their own participation
        # Captains can update participations for their events
        if not (request.user.is_c_suite or 
                request.user.is_captain or 
                participant.user == request.user):
            return Response(
                {'error': 'You do not have permission to update this participation'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def my_events(self, request):
        """Get current user's event participations"""
        participations = EventParticipant.objects.filter(user=request.user)
        serializer = self.get_serializer(participations, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm participation (Captains)"""
        if not request.user.role.can_manage_events:
            return Response(
                {'error': 'You do not have permission to confirm participations'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        participant = self.get_object()
        participant.status = 'CONFIRMED'
        participant.is_confirmed = True
        participant.save()
        
        return Response(EventParticipantSerializer(participant, context={'request': request}).data)
    
    @action(detail=True, methods=['post'])
    def mark_attendance(self, request, pk=None):
        """Mark attendance for event (Captains)"""
        if not request.user.role.can_manage_events:
            return Response(
                {'error': 'You do not have permission to mark attendance'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        participant = self.get_object()
        attended = request.data.get('attended', False)
        participant.status = 'ATTENDED' if attended else 'ABSENT'
        participant.save()
        
        return Response(EventParticipantSerializer(participant, context={'request': request}).data)