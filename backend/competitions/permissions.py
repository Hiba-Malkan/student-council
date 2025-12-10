from rest_framework import permissions


class CanManageCompetitions(permissions.BasePermission):
    """
    Permission to check if user can manage competitions.
    Staff, superusers, and users with specific role permissions can manage.
    """
    
    def has_permission(self, request, view):
        # Allow read operations for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # For write operations, check if user has management permissions
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Staff and superusers can always manage
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Check if user has role permission
        if hasattr(request.user, 'role') and request.user.role:
            return getattr(request.user.role, 'can_manage_competitions', False)
        
        return False
    
    def has_object_permission(self, request, view, obj):
        # Allow read operations for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Staff and superusers can edit/delete any competition
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Users with management permission can edit/delete
        if hasattr(request.user, 'role') and request.user.role:
            if getattr(request.user.role, 'can_manage_competitions', False):
                return True
        
        # Creators can edit/delete their own competitions
        return obj.created_by == request.user