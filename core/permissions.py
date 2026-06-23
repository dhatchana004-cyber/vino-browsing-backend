"""
Custom permission classes for role-based access control.
"""
from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """Only allow users with role='owner'."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'owner'
        )


class IsStaffRole(BasePermission):
    """Only allow users with role='staff'."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'staff'
        )


class IsOwnerOrReadOnly(BasePermission):
    """
    Owner gets full CRUD. Staff gets read-only access.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user.role == 'owner'


class IsOwnerOrSelf(BasePermission):
    """
    Owner can access all objects.
    Staff can only access objects where staff=request.user.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'owner':
            return True
        # Check if the object has a 'staff' field pointing to user
        if hasattr(obj, 'staff'):
            return obj.staff == request.user
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        return False
