from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Meeting, MinutesOfMeeting, MeetingAttendance
from .serializers import MeetingSerializer, MinutesOfMeetingSerializer, MeetingAttendanceSerializer
from accounts.permissions import CanScheduleMeetings


class MeetingViewSet(viewsets.ModelViewSet):
    """ViewSet for managing meetings"""
    queryset = Meeting.objects.all()
    serializer_class = MeetingSerializer
    filterset_fields = ['date', 'is_cancelled', 'organized_by']
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['date', 'created_at']
    ordering = ['date'] 

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'mom']:
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

    def perform_create(self, serializer):
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

    def perform_create(self, serializer):
        serializer.save(marked_by=self.request.user)
