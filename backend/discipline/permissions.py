from rest_framework import permissions


class IsDisciplineManager(permissions.BasePermission):
    """
    Permission to allow only staff members and users with can_record_discipline permission.
    All authenticated users can view records if they have can_view_discipline permission.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Read permissions for users with can_view_discipline
        if request.method in permissions.SAFE_METHODS:
            if request.user.is_staff or request.user.is_superuser:
                return True
            if request.user.role and request.user.role.can_view_discipline:
                return True
            return False
        
        # Write permissions for users with can_record_discipline
        if request.user.is_staff or request.user.is_superuser:
            return True
        if request.user.role and request.user.role.can_record_discipline:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Read permissions for users with can_view_discipline
        if request.method in permissions.SAFE_METHODS:
            if request.user.is_staff or request.user.is_superuser:
                return True
            if request.user.role and request.user.role.can_view_discipline:
                return True
            return False
        
        # Write permissions for staff, creator, or users with can_record_discipline
        if request.user.is_staff or request.user.is_superuser:
            return True
        if obj.created_by == request.user:
            return True
        if request.user.role and request.user.role.can_record_discipline:
            return True
        return False