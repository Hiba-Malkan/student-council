from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DisciplineOffenceViewSet, OffenceTypeViewSet,
    DefaulterReportViewSet, DisciplineActionViewSet
)

router = DefaultRouter()
router.register(r'offences', DisciplineOffenceViewSet, basename='offence')
router.register(r'offence-types', OffenceTypeViewSet, basename='offence-type')
router.register(r'defaulter-reports', DefaulterReportViewSet, basename='defaulter-report')
router.register(r'actions', DisciplineActionViewSet, basename='action')

urlpatterns = [
    path('', include(router.urls)),
]