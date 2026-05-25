from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'records', views.DisciplineRecordViewSet, basename='discipline')
router.register(r'offense-logs', views.OffenseLogViewSet, basename='offense')

urlpatterns = [
    path('', include(router.urls)),
]