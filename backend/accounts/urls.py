from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LoginView, LogoutView, CurrentUserView,
    UserViewSet, RoleViewSet,
    ForgotPasswordView, VerifyOTPView, ResetPasswordView,
    ContactAdminView, ContactMessageListView
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'roles', RoleViewSet, basename='role')

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', CurrentUserView.as_view(), name='current-user'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('contact-admin/', ContactAdminView.as_view(), name='contact-admin'),
    path('contact-messages/', ContactMessageListView.as_view(), name='contact-messages'),
    path('', include(router.urls)),
]