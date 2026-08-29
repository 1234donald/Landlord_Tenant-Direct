"""Role-based permission classes for the platform.

These classes enforce the three primary authorisation roles (TENANT, LANDLORD,
ADMIN) plus an ownership rule. Every protected endpoint is expected to declare
the appropriate permission class so that a user can never access functionality
belonging to another role (AGENTS 8, 19) and can only access their own
resources unless they are an administrator.
"""
from rest_framework.permissions import BasePermission


class IsTenant(BasePermission):
    """Allow access only to authenticated users with the TENANT role."""

    message = "Tenant access required."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_tenant)


class IsLandlord(BasePermission):
    """Allow access only to authenticated users with the LANDLORD role."""

    message = "Landlord access required."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_landlord)


class IsAdmin(BasePermission):
    """Allow access only to authenticated users with the ADMIN role."""

    message = "Administrator access required."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_admin)


class IsOwnerOrAdmin(BasePermission):
    """Allow access only to the owner of a resource or to an administrator.

    Requires prior authentication (in ``has_permission``) and then, per object,
    allows the owner of the resource or any administrator (``has_object_permission``).
    """

    message = "You do not have permission to access this resource."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_admin:
            return True
        return bool(hasattr(obj, "pk") and obj.pk == user.pk)
