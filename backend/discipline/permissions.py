from rest_framework import permissions


class IsDisciplineManager(permissions.BasePermission):
    """
    Permission to allow only staff members and discipline managers to create/edit records.
    All authenticated users can view records.
    """
    
    def has_permission(self, request, view):
        # Allow read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Write permissions only for staff or users with specific role
        return request.user and request.user.is_authenticated and (
            request.user.is_staff or 
            request.user.is_superuser or
            hasattr(request.user, 'role_detail') and 
            request.user.role_detail and 
            request.user.role_detail.name in ['President', 'Vice President', 'Discipline Manager']
        )

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Write permissions only for staff, creator, or authorized roles
        return request.user and request.user.is_authenticated and (
            request.user.is_staff or 
            request.user.is_superuser or
            obj.created_by == request.user or
            hasattr(request.user, 'role_detail') and 
            request.user.role_detail and 
            request.user.role_detail.name in ['President', 'Vice President', 'Discipline Manager']
        )