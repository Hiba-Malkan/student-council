from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AnnouncementViewSet, EventParticipantViewSet

router = DefaultRouter()
router.register(r'', AnnouncementViewSet, basename='announcement')
router.register(r'participants', EventParticipantViewSet, basename='participant')

urlpatterns = [
    path('', include(router.urls)),
]