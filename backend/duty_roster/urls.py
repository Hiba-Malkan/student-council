from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DutyViewSet, DutyTypeViewSet

router = DefaultRouter()
router.register(r'duties', DutyViewSet, basename='duty') 
router.register(r'duty-types', DutyTypeViewSet, basename='duty-type')  

urlpatterns = [
    path('', include(router.urls)),
]