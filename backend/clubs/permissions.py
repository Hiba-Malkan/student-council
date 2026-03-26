from rest_framework import permissions


class CanManageClubs(permissions.BasePermission):
    """
    Permission check for club management.
    Allows access if:
    - User is a superuser, OR
    - User's role has can_add_clubs permission
    """
    
    def has_permission(self, request, view):
        # Allow GET, HEAD, OPTIONS for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # For write operations, check permissions
        return (
            request.user.is_superuser or
            (hasattr(request.user, 'role') and 
             request.user.role and 
             getattr(request.user.role, 'can_add_clubs', False))
        )
    
    def has_object_permission(self, request, view, obj):
        # Allow GET, HEAD, OPTIONS for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # For write operations, check permissions
        return (
            request.user.is_superuser or
            (hasattr(request.user, 'role') and 
             request.user.role and 
             getattr(request.user.role, 'can_add_clubs', False))
        )


class CanViewClubSignups(permissions.BasePermission):
    """
    Strict permission for viewing and managing club signups.
    Only allows users with can_add_clubs permission (club managers/c-suite).
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and
            (request.user.is_superuser or
             (hasattr(request.user, 'role') and 
              request.user.role and 
              getattr(request.user.role, 'can_add_clubs', False)))
        )