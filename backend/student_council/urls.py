from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    # ============================================
    # ADMIN
    # ============================================
    path('admin/', admin.site.urls),
    
    # ============================================
    # REST API ENDPOINTS
    # ============================================
    path('api/accounts/', include('accounts.urls')),
    path('api/duty-roster/', include('duty_roster.urls')),
    path('api/', include('meetings.urls')),
    path('api/announcements/', include('announcements.urls')),
    path('api/discipline/', include('discipline.urls')),
    path('api/projects/', include('projects.urls')),
    path('api/notifications/', include('notifications.urls')),
    
    # ============================================
    # HTML PAGES (All CSS/JS inline in templates)
    # ============================================
    
    # Authentication
    path('', TemplateView.as_view(template_name='login.html'), name='login'),
    
    # Dashboard
    path('dashboard/', TemplateView.as_view(template_name='dashboard.html'), name='dashboard'),
    
    # Duties
    path('duties/', TemplateView.as_view(template_name='duties.html'), name='duties'),
    
    # Meetings
    path('meetings/', TemplateView.as_view(template_name='meetings.html'), name='meetings'),
    
    # Announcements
    path('announcements/', TemplateView.as_view(template_name='announcements.html'), name='announcements'),
    
    # Discipline
    path('discipline/', TemplateView.as_view(template_name='discipline.html'), name='discipline'),
    
    # Projects
    path('projects/', TemplateView.as_view(template_name='projects.html'), name='projects'),
    
    # Users/Profile
    path('profile/', TemplateView.as_view(template_name='profile.html'), name='profile'),
    
    # Notifications
    path('notifications/', TemplateView.as_view(template_name='notifications.html'), name='notifications'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)