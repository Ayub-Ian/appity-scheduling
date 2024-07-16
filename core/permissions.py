
from django.utils.translation import gettext_lazy as _

from rest_framework.permissions import BasePermission
from rest_framework import exceptions

class EndUserOnly(BasePermission):
    """
    Allows access only to end-users and raise 401 if user is admin(staff, superuser or reseller).
    """

    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            if request.user.is_admin:
                raise exceptions.AuthenticationFailed()
            else:
                return True
        else:
            return False

class StaffOnly(BasePermission):
    """
    Allows access only to users with is_staff flag set and raise 401 if flag is not set.
    """

    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            if request.user.is_staff:
                return True
            else:
                raise exceptions.AuthenticationFailed()
        else:
            return False

class SuperUserOnly(BasePermission):
    """
    Allows access only to users with is_superuser flag set and raise 401 if flag is not set.
    """

    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            if request.user.is_staff and request.user.is_superuser:
                return True
            else:
                raise exceptions.AuthenticationFailed('Unauthorized: missing superuser status')
        else:
            return False


class CustomPermissions(BasePermission):
    """
    The CustomPermissions class allows dynamic registering of permission classes.
    A permission class is any class that has one/all of the two functions: has_permissions
        and has_object_permissions.
    Place this class in a view as a permission class where you want all dynamic
        permissions to take effect.
    """
    message = _('Unable to perform the requested action')
    has_permission_instances = tuple()
    has_object_permission_instances = tuple()

    @staticmethod
    def register(permission_class):
        """Register a permission class instance"""
        if hasattr(permission_class, 'has_permission') and callable(permission_class.has_permission):
            CustomPermissions.has_permission_instances += (permission_class,)
        elif hasattr(permission_class,
                     'has_object_permission') and callable(permission_class.has_object_permission):
            CustomPermissions.has_object_permission_instances += (permission_class,)

    @staticmethod
    def unregister(permission_class):
        """Unregister an instance of a permission class"""
        cp = CustomPermissions
        cp.has_permission_instances = (c for c in cp.has_permission_instances if c != permission_class)
        cp.has_object_permission_instances = (c for c in cp.has_object_permission_instances if c != permission_class)

    def has_permission(self, request, view):
        """Call has_permission on all registered classes"""
        for cls in CustomPermissions.has_permission_instances:
            if not cls.has_permission(request, view):
                self.message = _('Unable to perform the requested action')
                if hasattr(cls, 'message'):
                    self.message = cls.message
                return False
        return True

    def has_object_permission(self, request, view, obj):
        """Call has_permission on all registered classes"""
        for cls in CustomPermissions.has_object_permission_instances:
            if not cls.has_object_permission(request, view, obj):
                self.message = _('Unable to perform the requested action')
                if hasattr(cls, 'message'):
                    self.message = cls.message
                return False
        return True
