from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone
from django.db.models import Q
from .models import Meeting, MinutesOfMeeting, MeetingAttendance
from .serializers import MeetingSerializer, MinutesOfMeetingSerializer, MeetingAttendanceSerializer
from accounts.permissions import CanScheduleMeetings, CanManageMeetings


def _can_manage_meetings(user):
    """Anyone with a role other than a normal student may manage meeting content."""
    if not user or not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser or user.is_c_suite:
        return True
    return bool(user.role) and not user.role.is_normal_student


def _can_fully_edit_meetings(user, meeting):
    """Full edit rights: staff, superusers, C-Suite, schedulers, or the organizer."""
    if not user or not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser or user.is_c_suite:
        return True
    if user.role and user.role.can_schedule_meetings:
        return True
    return meeting.organized_by == user


class MeetingViewSet(viewsets.ModelViewSet):
    """ViewSet for managing meetings"""
    queryset = Meeting.objects.all()
    serializer_class = MeetingSerializer
    filterset_fields = ['date', 'is_cancelled', 'organized_by']
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['date', 'created_at']
    ordering = ['date'] 

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'mom']:
            permission_classes = [IsAuthenticated, CanManageMeetings]
        elif self.action == 'destroy':
            permission_classes = [IsAuthenticated, CanScheduleMeetings]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = super().get_queryset()
        date_gte = self.request.query_params.get('date__gte')
        date_lt = self.request.query_params.get('date__lt')
        if date_gte:
            queryset = queryset.filter(date__gte=date_gte)
        if date_lt:
            queryset = queryset.filter(date__lt=date_lt)
        return queryset

    def perform_create(self, serializer):
        serializer.save(organized_by=self.request.user)
    
    def update(self, request, *args, **kwargs):
        """Only allow editing future meetings. Non-scheduler role holders may
        only change the agenda; anything else requires full edit rights."""
        meeting = self.get_object()
        
        # Check if meeting is in the past
        if meeting.date < timezone.now().date():
            return Response(
                {'detail': 'Cannot edit past meetings.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not _can_manage_meetings(request.user) and not _can_fully_edit_meetings(request.user, meeting):
            return Response(
                {'detail': 'Only the meeting organizer or staff can edit this meeting.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Agenda-only editors cannot alter any other meeting field
        if (
            _can_manage_meetings(request.user)
            and not _can_fully_edit_meetings(request.user, meeting)
            and set(request.data.keys()) - {'agenda'}
        ):
            return Response(
                {'detail': 'You may only update the meeting agenda.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        """Only allow editing future meetings. Non-scheduler role holders may
        only change the agenda; anything else requires full edit rights."""
        meeting = self.get_object()
        
        # Check if meeting is in the past
        if meeting.date < timezone.now().date():
            return Response(
                {'detail': 'Cannot edit past meetings.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not _can_manage_meetings(request.user) and not _can_fully_edit_meetings(request.user, meeting):
            return Response(
                {'detail': 'Only the meeting organizer or staff can edit this meeting.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Agenda-only editors cannot alter any other meeting field
        if (
            _can_manage_meetings(request.user)
            and not _can_fully_edit_meetings(request.user, meeting)
            and set(request.data.keys()) - {'agenda'}
        ):
            return Response(
                {'detail': 'You may only update the meeting agenda.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().partial_update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Only allow deleting future meetings and only by organizer or staff"""
        meeting = self.get_object()
        
        # Check if meeting is in the past
        if meeting.date < timezone.now().date():
            return Response(
                {'detail': 'Cannot delete past meetings.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if user is organizer or staff
        if meeting.organized_by != request.user and not request.user.is_staff:
            return Response(
                {'detail': 'Only the meeting organizer or staff can delete this meeting.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['get', 'post', 'delete'], url_path='mom')
    def mom(self, request, pk=None):
        """Manage Minutes of Meeting (GET, POST, DELETE)"""
        meeting = self.get_object()
        
        if request.method == 'GET':
            # Get MOM
            if not hasattr(meeting, 'mom'):
                return Response({'detail': 'No MOM exists.'}, status=status.HTTP_404_NOT_FOUND)
            serializer = MinutesOfMeetingSerializer(meeting.mom)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            # Upload/Create MOM
            if hasattr(meeting, 'mom'):
                return Response({'detail': 'MOM already exists.'}, status=status.HTTP_400_BAD_REQUEST)
            serializer = MinutesOfMeetingSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(meeting=meeting, uploaded_by=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'DELETE':
            # Delete MOM
            if not hasattr(meeting, 'mom'):
                return Response({'detail': 'No MOM exists.'}, status=status.HTTP_404_NOT_FOUND)
            meeting.mom.delete()
            return Response({'detail': 'MOM deleted.'}, status=status.HTTP_204_NO_CONTENT)


class MinutesOfMeetingViewSet(viewsets.ModelViewSet):
    """ViewSet for managing MOMs"""
    queryset = MinutesOfMeeting.objects.all()
    serializer_class = MinutesOfMeetingSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['meeting', 'uploaded_by', 'emailed_to_phase_heads']
    search_fields = ['content', 'action_items']
    ordering_fields = ['uploaded_at', 'created_at']
    ordering = ['-uploaded_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser or user.is_c_suite:
            return MinutesOfMeeting.objects.all()
        return MinutesOfMeeting.objects.filter(
            Q(meeting__organized_by=user) |
            Q(present=user) |
            Q(meeting__attendees=user) |
            Q(uploaded_by=user)
        ).distinct()

    def _can_manage(self, user, meeting):
        return (
            _can_manage_meetings(user) or
            (user.role and user.role.can_schedule_meetings) or
            meeting.organized_by == user
        )

    def perform_create(self, serializer):
        meeting = serializer.validated_data['meeting']
        if not self._can_manage(self.request.user, meeting):
            raise PermissionDenied('Only meeting organizers or schedulers can upload minutes.')
        serializer.save(uploaded_by=self.request.user)


class MeetingAttendanceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing attendance"""
    queryset = MeetingAttendance.objects.all()
    serializer_class = MeetingAttendanceSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['meeting', 'user', 'status']
    search_fields = ['notes']
    ordering_fields = ['created_at']
    ordering = ['meeting', 'user']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser or user.is_c_suite:
            return MeetingAttendance.objects.all()
        return MeetingAttendance.objects.filter(
            Q(meeting__organized_by=user) | Q(user=user)
        ).distinct()

    def perform_create(self, serializer):
        user = self.request.user
        meeting = serializer.validated_data['meeting']
        attendee = serializer.validated_data.get('user')
        can_manage = (
            user.is_staff or user.is_superuser or user.is_c_suite or
            (user.role and user.role.can_schedule_meetings) or
            meeting.organized_by == user
        )
        if not (can_manage or attendee == user):
            raise PermissionDenied('You can only mark attendance for yourself unless you manage meetings.')
        serializer.save(marked_by=user)

    def perform_update(self, serializer):
        user = self.request.user
        can_manage = (
            user.is_staff or user.is_superuser or user.is_c_suite or
            (user.role and user.role.can_schedule_meetings) or
            serializer.instance.meeting.organized_by == user
        )
        if not (can_manage or serializer.instance.user == user):
            raise PermissionDenied('You can only update your own attendance record.')
        serializer.save(marked_by=user)
