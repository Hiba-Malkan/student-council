from rest_framework.pagination import PageNumberPagination
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import GatePass
from .serializers import GatePassSerializer, GatePassApprovalSerializer
from .tasks import send_gate_pass_decision_email, send_gate_pass_submission_email
from rest_framework.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100

class GatePassViewSet(viewsets.ModelViewSet):
    serializer_class = GatePassSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        user = self.request.user
        
        # Users with permission see filtered requests based on status query param
        if self._can_manage_gatepass(user):
            queryset = GatePass.objects.all()
            
            # Filter by status if provided in query params
            status = self.request.query_params.get('status')
            if status:
                queryset = queryset.filter(status=status)
            
            return queryset
        
        # Students see only their own requests
        return GatePass.objects.filter(student=user)
    
    def _can_manage_gatepass(self, user):
        """Check if the user has the permission to manage gate passes."""
        return user.role and user.role.can_manage_gatepass
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            logger.error(f"Validation error on gate pass creation: {e.detail}", exc_info=True)
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            gatepass = GatePass.objects.create(
                student=request.user,
                dno=request.data.get('dno'),
                name=request.data.get('name'),
                student_class=request.data.get('student_class'),
                student_section=request.data.get('student_section'),
                parent_email=request.data.get('parent_email'),
                ct_email=request.data.get('ct_email'),
                requested_date=request.data.get('requested_date'),
                reason=request.data.get('reason')
            )
        except Exception as e:
            logger.error(f"Error creating gatepass object: {e}", exc_info=True)
            return Response(
                {'error': 'There was a problem creating the gate pass. Please check the data and try again.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Offload email sending to Celery
        send_gate_pass_submission_email.delay(gatepass.id)
            
        return Response(
            GatePassSerializer(gatepass).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def approve_or_deny(self, request, pk=None):
        gatepass = self.get_object()
        
        # Only users with the permission can approve/deny
        if not self._can_manage_gatepass(request.user):
            return Response(
                {'error': 'You do not have permission to approve gate pass requests.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = GatePassApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            gatepass.status = serializer.validated_data['status']
            gatepass.approved_by = request.user
            gatepass.approval_note = serializer.validated_data.get('note', '')
            gatepass.approval_timestamp = timezone.now()
            gatepass.save()
            
            # Asynchronously send email notifications
            send_gate_pass_decision_email.delay(gatepass.id)
            
            return Response(
                GatePassSerializer(gatepass).data,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': 'Failed to process gate pass. Please try again later.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_requests(self, request):
        requests = GatePass.objects.filter(student=request.user)
        serializer = self.get_serializer(requests, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='processed-requests')
    def processed_requests(self, request):
        """
        Returns paginated, processed (approved or denied) gate pass requests.
        """
        if not self._can_manage_gatepass(request.user):
            return Response(
                {'error': 'You do not have permission to view these requests.'},
                status=status.HTTP_403_FORBIDDEN
            )

        processed = GatePass.objects.filter(status__in=['approved', 'denied']).order_by('-approval_timestamp')
        
        # Paginate the queryset
        page = self.paginate_queryset(processed)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(processed, many=True)
        return Response(serializer.data)
