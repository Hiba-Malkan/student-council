from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProjectViewSet, ProjectAttachmentViewSet, ProjectMilestoneViewSet,
    ProjectUpdateViewSet, PurchaseViewSet
)

router = DefaultRouter()
router.register(r'', ProjectViewSet, basename='project')
router.register(r'attachments', ProjectAttachmentViewSet, basename='attachment')
router.register(r'milestones', ProjectMilestoneViewSet, basename='milestone')
router.register(r'updates', ProjectUpdateViewSet, basename='update')
router.register(r'purchases', PurchaseViewSet, basename='purchase')

urlpatterns = [
    path('', include(router.urls)),
]