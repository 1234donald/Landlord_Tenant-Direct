"""Permission classes for the Apartment module (Phase 3, Sprint 3.5).

The ownership rule ensures a user can only modify their own listings and that
an administrator may manage any listing (AGENTS 8, 19). A tenant or another
landlord can never modify a listing they do not own.
"""
from rest_framework.permissions import BasePermission


class IsApartmentOwnerOrAdmin(BasePermission):
    """Allow access only to an apartment's owning landlord or an administrator.

    Requires prior authentication (in ``has_permission``) and then, per object,
    allows the owning landlord or any administrator (``has_object_permission``).
    """

    message = "You do not have permission to manage this apartment."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_admin:
            return True
        return bool(hasattr(obj, "landlord") and obj.landlord_id == user.id)
