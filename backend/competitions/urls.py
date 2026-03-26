from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.views.generic import TemplateView
from . import views

# API Router
router = DefaultRouter()
router.register(r'competitions', views.CompetitionViewSet, basename='competition')

# HTML URL patterns (must come AFTER API routes to avoid shadowing)
html_urlpatterns = [
    path('competitions/new/', TemplateView.as_view(template_name='competitions/new_competition.html'), name='new_competition'),
    path('competitions/edit/<int:pk>/', TemplateView.as_view(template_name='competitions/edit_competition.html'), name='edit_competition'),
    path('competitions/detail/<int:pk>/', TemplateView.as_view(template_name='competitions/competition_detail.html'), name='competition_detail'),
    path('competitions/signups/', views.CompetitionSignupsView.as_view(), name='competition_signups'),
    path('competitions/', TemplateView.as_view(template_name='competitions/competitions.html'), name='competitions'),
]

# Combine API and HTML URL patterns (API routes first so they take precedence)
urlpatterns = router.urls + html_urlpatterns