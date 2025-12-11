from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.DisciplineRecordViewSet, basename='discipline')
router.register(r'offense', views.OffenseLogViewSet, basename='offense')

urlpatterns = [
    path('', include(router.urls)),
]