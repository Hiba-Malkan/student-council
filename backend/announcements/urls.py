from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AnnouncementViewSet, EventParticipantViewSet, PublicAnnouncementViewSet

router = DefaultRouter()
router.register(r'participants', EventParticipantViewSet, basename='participant')
router.register(r'public', PublicAnnouncementViewSet, basename='public-announcement')
router.register(r'', AnnouncementViewSet, basename='announcement')

urlpatterns = [
    path('', include(router.urls)),
]
