"""Permission classes for the Messaging module (Phase 4, Sprint 4.5).

Messaging is private to the two conversation participants and to
administrators. A tenant or landlord may only view conversations and messages
they are a participant of, and may only send a message within a conversation
they belong to. Another user can never read or send in a conversation they are
not part of (AGENTS 8, 19).
"""
from rest_framework.permissions import BasePermission


class IsConversationParticipantOrAdmin(BasePermission):
    """Allow access only to a conversation's participants or an administrator.

    Requires prior authentication and then, per object, allows the owning
    tenant or landlord of the conversation, or any administrator
    (``has_object_permission``).
    """

    message = "You do not have permission to access this conversation."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_admin:
            return True
        return bool(obj.is_participant(user))


class IsParticipantForMessage(BasePermission):
    """Allow access only to a message's sender/recipient or an administrator.

    Requires prior authentication and then, per object, allows the sender or
    the recipient of the message, or any administrator
    (``has_object_permission``).
    """

    message = "You do not have permission to access this message."

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
            hasattr(obj, "sender") and hasattr(obj, "recipient")
            and (obj.sender_id == user.id or obj.recipient_id == user.id)
        )
