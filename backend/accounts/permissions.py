from rest_framework import permissions


class IsCSuite(permissions.BasePermission):
    """Permission class for C-Suite only access"""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            getattr(request.user, 'is_c_suite', False)
        )


class IsCSuiteOrStaff(permissions.BasePermission):
    """Permission to check if user is C-Suite or staff"""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_staff or 
             request.user.is_superuser or 
             getattr(request.user, 'is_c_suite', False))
        )


class IsCaptainOrCSuite(permissions.BasePermission):
    """Permission class for Captains and C-Suite"""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (getattr(request.user, 'is_captain', False) or 
             getattr(request.user, 'is_c_suite', False))
        )


class IsPhaseHeadOrCSuite(permissions.BasePermission):
    """Permission class for Phase Heads and C-Suite"""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (getattr(request.user, 'is_phase_head', False) or 
             getattr(request.user, 'is_c_suite', False))
        )


class CanEditDutyRoster(permissions.BasePermission):
    """Permission to check if user can edit duty roster"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Staff and superusers can always edit
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Check for C-Suite access
        if getattr(request.user, 'is_c_suite', False):
            return True
        
        # Check role permission (supports both 'role' and 'role_detail')
        role = getattr(request.user, 'role', None) or getattr(request.user, 'role_detail', None)
        if role:
            return getattr(role, 'can_edit_duty_roster', False)
        
        return False


class CanScheduleMeetings(permissions.BasePermission):
    """Permission to check if user can schedule meetings"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Staff and superusers can always schedule
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Check for C-Suite access
        if getattr(request.user, 'is_c_suite', False):
            return True
        
        # Check role permission (supports both 'role' and 'role_detail')
        role = getattr(request.user, 'role', None) or getattr(request.user, 'role_detail', None)
        if role:
            return getattr(role, 'can_schedule_meetings', False)
        
        return False


class CanRecordDiscipline(permissions.BasePermission):
    """Permission to record discipline offences"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Staff and superusers can always record
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Check for C-Suite access
        if getattr(request.user, 'is_c_suite', False):
            return True
        
        # Check role permission (supports both 'role' and 'role_detail')
        role = getattr(request.user, 'role', None) or getattr(request.user, 'role_detail', None)
        if role:
            return getattr(role, 'can_record_discipline', False)
        
        return False


class CanManageAnnouncements(permissions.BasePermission):
    """Permission to check if user can manage announcements"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Staff and superusers can always manage
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Check for C-Suite access
        if getattr(request.user, 'is_c_suite', False):
            return True
        
        # Check role permission (supports both 'role' and 'role_detail')
        role = getattr(request.user, 'role', None) or getattr(request.user, 'role_detail', None)
        if role:
            return getattr(role, 'can_manage_announcements', False)
        
        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` or `created_by` attribute.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Staff and superusers can edit anything
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Check if object has owner/created_by field
        owner = getattr(obj, 'owner', None) or getattr(obj, 'created_by', None) or getattr(obj, 'organized_by', None)
        return owner == request.user


class IsOwner(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to access it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Staff and superusers can access anything
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Check if object has owner/created_by field
        owner = getattr(obj, 'owner', None) or getattr(obj, 'created_by', None) or getattr(obj, 'user', None)
        return owner == request.user