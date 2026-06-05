from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from clubs.urls import html_urlpatterns as clubs_html_urls
from competitions.urls import html_urlpatterns as competitions_html_urls
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_send_pending_emails(request):
    """Manually flush the pending email queue — useful for testing."""
    from notifications.tasks import send_pending_email_notifications
    result = send_pending_email_notifications()
    return Response({'result': result})


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
    path('api/notifications/send-pending/', trigger_send_pending_emails, name='send-pending-emails'),
    path('api/clubs/', include('clubs.urls')),
    path('api/', include('competitions.urls')),
    path('api/gatepass/', include('gatepass.urls')),
    path('api/feedback/', include('feedback.urls')),

    # ============================================
    # HTML PAGES
    # ============================================

    # Authentication & Home
    path('', TemplateView.as_view(template_name='login.html'), name='login'),
    path('forgot-password/', TemplateView.as_view(template_name='forgot_password.html'), name='forgot-password'),
    path('contact-admin/', TemplateView.as_view(template_name='contact_admin.html'), name='contact-admin'),

    # Dashboard
    path('dashboard/', TemplateView.as_view(template_name='dashboard.html'), name='dashboard'),

    # About
    path('about/', TemplateView.as_view(template_name='about.html'), name='about'),

    # Announcements
    path('announcements/', TemplateView.as_view(template_name='announcements/announcements.html'), name='announcements'),
    path('announcements/new/', TemplateView.as_view(template_name='announcements/new_announcement.html'), name='new_announcement'),
    path('announcements/edit/<int:pk>/', TemplateView.as_view(template_name='announcements/edit_announcement.html'), name='edit_announcement'),
    path('announcements/detail/<int:pk>/', TemplateView.as_view(template_name='announcements/announcement_detail.html'), name='announcement_detail'),

    # Clubs
    path('clubs/', include(clubs_html_urls)),

    # Competitions
    path('', include(competitions_html_urls)),

    # Duties
    path('duties/', TemplateView.as_view(template_name='duty-roster/duty_roster.html'), name='duty-roster'),
    path('duty-roster/', TemplateView.as_view(template_name='duty-roster/duty_roster.html'), name='duty_roster'),

    # Meetings
    path('meetings/', TemplateView.as_view(template_name='meetings/meetings.html'), name='meetings'),

    # Gate Pass
    path('gatepass/', TemplateView.as_view(template_name='gatepass.html'), name='gatepass'),

    # Discipline
    path('discipline/', TemplateView.as_view(template_name='discipline/discipline.html'), name='discipline'),
    path('discipline/new/', TemplateView.as_view(template_name='discipline/discipline_form.html'), name='new_discipline'),
    path('discipline/edit/<int:pk>/', TemplateView.as_view(template_name='discipline/discipline_edit.html'), name='edit_discipline'),
    path('discipline/detail/<int:pk>/', TemplateView.as_view(template_name='discipline/discipline_details.html'), name='discipline-detail'),

    # Users/Profile
    path('profile/', TemplateView.as_view(template_name='profile.html'), name='profile'),

    # Notifications
    path('notifications/', TemplateView.as_view(template_name='notifications.html'), name='notifications'),

    # Feedback
    path('feedback/', TemplateView.as_view(template_name='feedback.html'), name='feedback'),
    #Contacty Messages
    path('contact-messages/', TemplateView.as_view(template_name='contact_messages.html'), name='contact-messages'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)