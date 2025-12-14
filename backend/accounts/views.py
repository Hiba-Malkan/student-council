from rest_framework import generics, status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import User, Role, PasswordResetOTP, ContactMessage
from .serializers import (
    UserSerializer, RoleSerializer, LoginSerializer, RegisterSerializer,
    ForgotPasswordSerializer, VerifyOTPSerializer, ResetPasswordSerializer,
    ContactMessageSerializer
)


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(generics.GenericAPIView):
    """User login endpoint"""
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer
    authentication_classes = []
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        user = authenticate(username=username, password=password)
        
        if user is None:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active:
            return Response(
                {'error': 'Account is disabled'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })


class LogoutView(generics.GenericAPIView):
    """User logout endpoint"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CurrentUserView(generics.RetrieveUpdateAPIView):
    """Get and update current user profile"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_object(self):
        return self.request.user


class UserViewSet(viewsets.ModelViewSet):
    """CRUD operations for users (C-Suite only)"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['role', 'grade', 'section', 'house']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    def get_queryset(self):
        if self.request.user.is_c_suite or self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)
    
    @action(detail=True, methods=['post'])
    def assign_role(self, request, pk=None):
        """Assign role to user (C-Suite only)"""
        if not request.user.is_c_suite:
            return Response(
                {'error': 'Only C-Suite can assign roles'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.get_object()
        role_id = request.data.get('role_id')
        
        try:
            role = Role.objects.get(id=role_id)
            user.role = role
            user.save()
            return Response(UserSerializer(user).data)
        except Role.DoesNotExist:
            return Response(
                {'error': 'Role not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class RoleViewSet(viewsets.ModelViewSet):
    """CRUD operations for roles (C-Suite only)"""
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['category', 'level']
    search_fields = ['name', 'description']
    
    def get_queryset(self):
        return Role.objects.all()
    
    def create(self, request, *args, **kwargs):
        if not request.user.is_c_suite:
            return Response(
                {'error': 'Only C-Suite can create roles'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        if not request.user.is_c_suite:
            return Response(
                {'error': 'Only C-Suite can update roles'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        if not request.user.is_c_suite:
            return Response(
                {'error': 'Only C-Suite can delete roles'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


class ForgotPasswordView(generics.GenericAPIView):
    """
    Send OTP to user's email for password reset
    """
    serializer_class = ForgotPasswordSerializer
    permission_classes = [AllowAny]
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        ip_address = self.get_client_ip(request)
        
        # Create OTP
        otp_obj = PasswordResetOTP.create_otp(user, ip_address)
        
        # Send email
        try:
            subject = 'Password Reset OTP - Student Council'
            message = f"""
Hello {user.get_full_name() or user.username},

You have requested to reset your password. Your OTP code is:

{otp_obj.otp}

This code will expire in 10 minutes.

If you did not request this, please ignore this email and your password will remain unchanged.

Best regards,
Student Council Team
            """
            
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )
            
            return Response({
                'message': 'OTP has been sent to your email',
                'email': user.email
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Delete the OTP if email fails
            otp_obj.delete()
            return Response({
                'error': 'Failed to send email. Please try again later.',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyOTPView(generics.GenericAPIView):
    """
    Verify OTP without resetting password (optional step)
    """
    serializer_class = VerifyOTPSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        identifier = serializer.validated_data['identifier']
        otp = serializer.validated_data['otp']
        
        # Find user
        try:
            user = User.objects.get(email=identifier)
        except User.DoesNotExist:
            try:
                user = User.objects.get(username=identifier)
            except User.DoesNotExist:
                return Response({
                    'error': 'Invalid credentials'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify OTP
        try:
            otp_obj = PasswordResetOTP.objects.get(
                user=user,
                otp=otp,
                is_used=False
            )
            
            if not otp_obj.is_valid():
                return Response({
                    'error': 'OTP has expired'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'message': 'OTP verified successfully'
            }, status=status.HTTP_200_OK)
            
        except PasswordResetOTP.DoesNotExist:
            return Response({
                'error': 'Invalid OTP'
            }, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(generics.GenericAPIView):
    """
    Reset password using OTP
    """
    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        identifier = serializer.validated_data['identifier']
        otp = serializer.validated_data['otp']
        new_password = serializer.validated_data['new_password']
        
        # Find user
        try:
            user = User.objects.get(email=identifier)
        except User.DoesNotExist:
            try:
                user = User.objects.get(username=identifier)
            except User.DoesNotExist:
                return Response({
                    'error': 'Invalid credentials'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify OTP and reset password
        try:
            otp_obj = PasswordResetOTP.objects.get(
                user=user,
                otp=otp,
                is_used=False
            )
            
            if not otp_obj.is_valid():
                return Response({
                    'error': 'OTP has expired'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Reset password
            user.set_password(new_password)
            user.save()
            
            # Mark OTP as used
            otp_obj.mark_as_used()
            
            return Response({
                'message': 'Password has been reset successfully'
            }, status=status.HTTP_200_OK)
            
        except PasswordResetOTP.DoesNotExist:
            return Response({
                'error': 'Invalid OTP'
            }, status=status.HTTP_400_BAD_REQUEST)


class ContactAdminView(generics.CreateAPIView):
    """
    Allow users to contact administrators
    """
    serializer_class = ContactMessageSerializer
    permission_classes = [AllowAny]
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get client info
        ip_address = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Save the message
        contact_message = serializer.save(
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Send notification email to admins
        try:
            from django.core.mail import send_mail
            
            admin_emails = User.objects.filter(
                is_staff=True, is_active=True
            ).values_list('email', flat=True)
            
            if admin_emails:
                subject = f'New Contact Message: {contact_message.subject}'
                message = f"""
New contact message received:

From: {contact_message.name}
Email: {contact_message.email}
Username: {contact_message.username or 'Not provided'}

Subject: {contact_message.subject}

Message:
{contact_message.message}

---
Submitted at: {contact_message.created_at.strftime('%Y-%m-%d %H:%M:%S')}
IP Address: {ip_address}

Please respond via the admin panel: {request.build_absolute_uri('/admin/accounts/contactmessage/')}
                """
                
                send_mail(
                    subject,
                    message,
                    settings.EMAIL_HOST_USER,
                    list(admin_emails),
                    fail_silently=True,
                )
        except Exception as e:
            # Don't fail if email notification fails
            pass
        
        return Response({
            'message': 'Your message has been sent successfully. An administrator will contact you soon.',
            'id': contact_message.id
        }, status=status.HTTP_201_CREATED)


class ContactMessageListView(generics.ListAPIView):
    """
    View for admins to see all contact messages
    """
    serializer_class = ContactMessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Only staff/admin can view messages
        if not self.request.user.is_staff:
            return ContactMessage.objects.none()
        return ContactMessage.objects.all()