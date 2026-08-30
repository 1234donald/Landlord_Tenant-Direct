"""Permission classes for the Tenant Preference module (Phase 4, Sprint 4.4).

The ownership rule ensures a tenant can only manage their own preferences and
that an administrator may manage any preference (AGENTS 8, 19). Another tenant
or a landlord can never access a preference they do not own.
"""
from rest_framework.permissions import BasePermission


class IsPreferenceOwnerOrAdmin(BasePermission):
    """Allow access only to a preference's owning tenant or an administrator.

    Requires prior authentication and, per object, allows the owning tenant or
    any administrator.
    """

    message = "You do not have permission to manage this preference."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_admin:
            return True
        return bool(
            hasattr(obj, "tenant")
            and obj.tenant_id == user.id
            and user.is_tenant
        )
