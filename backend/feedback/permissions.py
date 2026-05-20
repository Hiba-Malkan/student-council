from rest_framework import permissions


class CanManageFeedback(permissions.BasePermission):
    """
    Permission to check if user can manage feedback.
    Staff, superusers, and users with specific role permissions can manage/view.
    Regular users can only submit feedback.
    """
    
    def has_permission(self, request, view):
        # Allow creating feedback for everyone (authenticated or not)
        if request.method == 'POST' and view.action == 'create':
            return True
        
        # For listing/retrieving, check if user has view permission
        if request.method in permissions.SAFE_METHODS:
            # Staff and superusers can view all
            if request.user and request.user.is_authenticated:
                if request.user.is_staff or request.user.is_superuser:
                    return True
                
                # Check if user has role permission to manage feedback
                if hasattr(request.user, 'role') and request.user.role:
                    if getattr(request.user.role, 'can_manage_feedback', False):
                        return True
                
                # Allow viewing detail (but will be restricted by has_object_permission)
                if view.action == 'retrieve':
                    return True
            
            # For list action, normal users can't view
            if view.action == 'list':
                return False
            
            # For other safe methods on list, restrict
            return False
        
        # For other operations (POST to custom actions), check if user has management permissions
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Staff and superusers can always manage
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Check if user has role permission
        if hasattr(request.user, 'role') and request.user.role:
            return getattr(request.user.role, 'can_manage_feedback', False)
        
        return False
    
    def has_object_permission(self, request, view, obj):
        # Staff and superusers can view/edit any feedback
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Users with management permission can view/edit
        if hasattr(request.user, 'role') and request.user.role:
            if getattr(request.user.role, 'can_manage_feedback', False):
                return True
        
        # Users can only view their own feedback if they have the role
        if request.method in permissions.SAFE_METHODS:
            return obj.submitted_by == request.user or obj.email == getattr(request.user, 'email', '')
        
        return False


class CanCreateFeedback(permissions.BasePermission):
    """Allow anyone to create feedback"""
    
    def has_permission(self, request, view):
        return request.method == 'POST'
