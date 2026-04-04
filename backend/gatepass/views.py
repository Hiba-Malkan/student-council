from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.core.mail import send_mail
from .models import GatePass
from .serializers import GatePassSerializer, GatePassApprovalSerializer

class GatePassViewSet(viewsets.ModelViewSet):
    serializer_class = GatePassSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Gate Pass Manager sees all requests
        if self.is_gatepass_manager(user):
            return GatePass.objects.all()
        
        # Students see only their own requests
        return GatePass.objects.filter(student=user)
    
    def is_gatepass_manager(self, user):
        return user.role and user.role.name == 'Gate Pass Manager'
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            gatepass = GatePass.objects.create(
                student=request.user,
                reason=request.data.get('reason')
            )
            
            # Send email to student
            send_mail(
                subject='Gate Pass Request Submitted',
                message=f'Your gate pass request has been submitted.\nReason: {gatepass.reason}',
                from_email='noreply@studentcouncil.com',
                recipient_list=[request.user.email],
                fail_silently=True
            )
            
            # Send email to gate pass managers
            from accounts.models import Role
            try:
                manager_role = Role.objects.get(name='Gate Pass Manager')
                managers = manager_role.users.all()
                manager_emails = [m.email for m in managers]
                if manager_emails:
                    send_mail(
                        subject='New Gate Pass Request',
                        message=f'New gate pass request from {request.user.get_full_name() or request.user.username}.\nReason: {gatepass.reason}',
                        from_email='noreply@studentcouncil.com',
                        recipient_list=manager_emails,
                        fail_silently=True
                    )
            except Role.DoesNotExist:
                pass
            
            return Response(
                GatePassSerializer(gatepass).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'error': 'Failed to submit gate pass request. Please try again later.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def approve_or_deny(self, request, pk=None):
        gatepass = self.get_object()
        
        # Only gate pass managers can approve/deny
        if not self.is_gatepass_manager(request.user):
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
            
            # Send email to student
            status_text = 'Approved' if gatepass.status == 'approved' else 'Denied'
            message = f'Your gate pass request has been {status_text.lower()}.\n\n'
            message += f'Reason for request: {gatepass.reason}\n\n'
            if gatepass.approval_note:
                message += f'Note from manager: {gatepass.approval_note}'
            
            send_mail(
                subject=f'Gate Pass Request {status_text}',
                message=message,
                from_email='noreply@studentcouncil.com',
                recipient_list=[gatepass.student.email],
                fail_silently=True
            )
            
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
