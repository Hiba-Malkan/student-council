from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, NotificationPreferenceViewSet, EmailTemplateViewSet

router = DefaultRouter()
router.register(r'', NotificationViewSet, basename='notification')
router.register(r'preferences', NotificationPreferenceViewSet, basename='preference')
router.register(r'email-templates', EmailTemplateViewSet, basename='email-template')

urlpatterns = [
    path('', include(router.urls)),
]