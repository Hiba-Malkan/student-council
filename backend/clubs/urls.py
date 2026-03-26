from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClubViewSet, ClubsOverviewView, ClubFormView, ClubSignupsView

# API Router
router = DefaultRouter()
router.register(r'', ClubViewSet, basename='club')

app_name = 'clubs'

# HTML URL patterns (for frontend views)
html_urlpatterns = [
    path('', ClubsOverviewView.as_view(), name='clubs_list'),
    path('new/', ClubFormView.as_view(), name='club_create'),
    path('edit/<int:pk>/', ClubFormView.as_view(), name='club_edit'),
    path('signups/', ClubSignupsView.as_view(), name='club_signups'),
]

# API URL patterns (for REST API)
urlpatterns = [
    path('', include(router.urls)),
]