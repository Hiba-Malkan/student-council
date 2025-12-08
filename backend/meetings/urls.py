from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MeetingViewSet, MinutesOfMeetingViewSet, MeetingAttendanceViewSet

router = DefaultRouter()
router.register(r'meetings', MeetingViewSet, basename='meeting')
router.register(r'mom', MinutesOfMeetingViewSet, basename='mom')
router.register(r'attendance', MeetingAttendanceViewSet, basename='attendance')

urlpatterns = [
    path('', include(router.urls)),  # just include the router here
]
