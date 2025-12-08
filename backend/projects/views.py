from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from datetime import date, timedelta
from .models import Project, ProjectAttachment, ProjectMilestone, ProjectUpdate, Purchase
from .serializers import (
    ProjectSerializer, ProjectAttachmentSerializer, ProjectMilestoneSerializer,
    ProjectUpdateSerializer, PurchaseSerializer
)


class ProjectViewSet(viewsets.ModelViewSet):
    """CRUD operations for projects"""
    queryset = Project.objects.prefetch_related('assigned_to', 'attachments', 'milestones')
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'project_type']
    search_fields = ['title', 'description']
    
    def get_queryset(self):
        user = self.request.user
        queryset = Project.objects.prefetch_related('assigned_to', 'attachments', 'milestones')
        
        # Users see projects they're assigned to or proposed
        if not user.is_c_suite:
            queryset = queryset.filter(
                Q(proposed_by=user) | Q(assigned_to=user)
            ).distinct()
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        if not request.user.role.can_create_projects:
            return Response(
                {'error': 'You do not have permission to create projects'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        request.data['proposed_by'] = request.user.id
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        project = self.get_object()
        
        # Check if user can update this project
        if not (request.user.is_c_suite or project.proposed_by == request.user):
            return Response(
                {'error': 'You do not have permission to update this project'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def pending_approval(self, request):
        """Get projects pending approval (C-Suite)"""
        if not request.user.is_c_suite:
            return Response(
                {'error': 'Only C-Suite can view pending approvals'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        projects = Project.objects.filter(status='PENDING_APPROVAL')
        serializer = self.get_serializer(projects, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming_deadlines(self, request):
        """Get projects with upcoming deadlines"""
        upcoming = date.today() + timedelta(days=7)
        projects = self.get_queryset().filter(
            deadline__lte=upcoming,
            deadline__gte=date.today(),
            status__in=['APPROVED', 'IN_PROGRESS']
        )
        
        serializer = self.get_serializer(projects, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a project (C-Suite only)"""
        if not request.user.role.can_approve_projects:
            return Response(
                {'error': 'You do not have permission to approve projects'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        project = self.get_object()
        project.status = 'APPROVED'
        project.approved_by = request.user
        project.approved_at = timezone.now()
        project.approval_notes = request.data.get('notes', '')
        project.save()
        
        return Response(ProjectSerializer(project).data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a project (C-Suite only)"""
        if not request.user.role.can_approve_projects:
            return Response(
                {'error': 'You do not have permission to reject projects'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        project = self.get_object()
        project.status = 'REJECTED'
        project.rejection_reason = request.data.get('reason', '')
        project.save()
        
        return Response(ProjectSerializer(project).data)
    
    @action(detail=True, methods=['post'])
    def submit_for_approval(self, request, pk=None):
        """Submit project for approval"""
        project = self.get_object()
        
        if project.proposed_by != request.user and not request.user.is_c_suite:
            return Response(
                {'error': 'You do not have permission to submit this project'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        project.status = 'PENDING_APPROVAL'
        project.save()
        
        return Response(ProjectSerializer(project).data)
    
    @action(detail=True, methods=['post'])
    def mark_complete(self, request, pk=None):
        """Mark project as completed"""
        project = self.get_object()
        
        if not (request.user.is_c_suite or project.proposed_by == request.user):
            return Response(
                {'error': 'You do not have permission to complete this project'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        project.status = 'COMPLETED'
        project.completion_date = timezone.now().date()
        project.actual_cost = request.data.get('actual_cost', project.estimated_budget)
        project.save()
        
        return Response(ProjectSerializer(project).data)


class ProjectAttachmentViewSet(viewsets.ModelViewSet):
    """Manage project attachments"""
    queryset = ProjectAttachment.objects.select_related('project', 'uploaded_by')
    serializer_class = ProjectAttachmentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['project']
    
    def create(self, request, *args, **kwargs):
        request.data['uploaded_by'] = request.user.id
        return super().create(request, *args, **kwargs)


class ProjectMilestoneViewSet(viewsets.ModelViewSet):
    """Manage project milestones"""
    queryset = ProjectMilestone.objects.select_related('project', 'assigned_to')
    serializer_class = ProjectMilestoneSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['project', 'is_completed']
    
    @action(detail=True, methods=['post'])
    def mark_complete(self, request, pk=None):
        """Mark milestone as completed"""
        milestone = self.get_object()
        milestone.is_completed = True
        milestone.completed_at = timezone.now()
        milestone.save()
        
        return Response(ProjectMilestoneSerializer(milestone).data)


class ProjectUpdateViewSet(viewsets.ModelViewSet):
    """Post and view project updates"""
    queryset = ProjectUpdate.objects.select_related('project', 'posted_by')
    serializer_class = ProjectUpdateSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['project']
    
    def create(self, request, *args, **kwargs):
        request.data['posted_by'] = request.user.id
        return super().create(request, *args, **kwargs)


class PurchaseViewSet(viewsets.ModelViewSet):
    """Manage purchases within projects"""
    queryset = Purchase.objects.select_related('project', 'purchased_by')
    serializer_class = PurchaseSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['project', 'status']
    
    def create(self, request, *args, **kwargs):
        request.data['purchased_by'] = request.user.id
        return super().create(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def mark_received(self, request, pk=None):
        """Mark purchase as received"""
        purchase = self.get_object()
        purchase.status = 'RECEIVED'
        purchase.save()
        
        return Response(PurchaseSerializer(purchase).data)