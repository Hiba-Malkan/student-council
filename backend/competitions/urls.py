from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.views.generic import TemplateView
from . import views

# API Router
router = DefaultRouter()
router.register(r'competitions', views.CompetitionViewSet, basename='competition')

# HTML URL patterns
html_urlpatterns = [
    path('competitions/', TemplateView.as_view(template_name='competitions.html'), name='competitions'),
    path('competitions/new/', TemplateView.as_view(template_name='new_competition.html'), name='new_competition'),
    path('competitions/edit/<int:pk>/', TemplateView.as_view(template_name='edit_competition.html'), name='edit_competition'),
    path('competitions/detail/<int:pk>/', TemplateView.as_view(template_name='competition_detail.html'), name='competition_detail'),
]

# API URL patterns
urlpatterns = router.urls