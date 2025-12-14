from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from clubs.urls import html_urlpatterns as clubs_html_urls
from competitions.urls import html_urlpatterns as competitions_html_urls
from discipline import views as discipline_views

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
    path('api/notifications/', include('notifications.urls')),
    path('api/clubs/', include('clubs.urls')),  # ← Clubs API
    path('api/', include('competitions.urls')),  # ← Competitions API
    
    # ============================================
    # HTML PAGES (All CSS/JS inline in templates)
    # ============================================
    
    # Authentication & Home
    path('', TemplateView.as_view(template_name='login.html'), name='login'),
    path('forgot-password/', TemplateView.as_view(template_name='forgot_password.html'), name='forgot-password'),
    path('contact-admin/', TemplateView.as_view(template_name='contact_admin.html'), name='contact-admin'),
    
    # Dashboard
    path('dashboard/', TemplateView.as_view(template_name='dashboard.html'), name='dashboard'),
    
    # Announcements
    path('announcements/', TemplateView.as_view(template_name='announcements/announcements.html'), name='announcements'),
    path('announcements/new/', TemplateView.as_view(template_name='announcements/new_announcement.html'), name='new_announcement'),
    path('announcements/edit/<int:pk>/', TemplateView.as_view(template_name='announcements/edit_announcement.html'), name='edit_announcement'),
    path('announcements/detail/<int:pk>/', TemplateView.as_view(template_name='announcements/announcement_detail.html'), name='announcement_detail'),
    
    # Clubs HTML pages
    path('clubs/', include(clubs_html_urls)),
    
    # Competitions HTML pages
    path('', include(competitions_html_urls)),
    
    # Duties
    path('duties/', TemplateView.as_view(template_name='duty-roster/duty_roster.html'), name='duty-roster'),
    path('duty-roster/', TemplateView.as_view(template_name='duty-roster/duty_roster.html'), name='duty_roster'),
    
    # Meetings
    path('meetings/', TemplateView.as_view(template_name='meetings/meetings.html'), name='meetings'),
    
    # Discipline
    path('discipline/', TemplateView.as_view(template_name='discipline/discipline.html'), name='discipline'),
    path('discipline/new/', TemplateView.as_view(template_name='discipline/discipline_form.html'), name='new_discipline'),
    path('discipline/edit/<int:pk>/', TemplateView.as_view(template_name='discipline/discipline_edit.html'), name='edit_discipline'),
    path('discipline/detail/<int:pk>/', TemplateView.as_view(template_name='discipline/discipline_details.html'), 
         name='discipline-detail'),
    
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