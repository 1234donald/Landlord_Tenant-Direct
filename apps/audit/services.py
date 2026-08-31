"""Audit event logging service (Phase 6, Sprint 6.5).

Provides helper functions for emitting audit events from any part of the
application.  Each function creates an ``AuditEvent`` record without
performing any additional side-effects, keeping the audit layer purely
observational (AGENTS 6 — business logic stays out of the audit service).

Usage::

    from apps.audit.services import log_auth_event, log_admin_event

    log_auth_event(
        action="Login successful",
        user=request.user,
        ip_address=get_client_ip(request),
    )
"""
import logging

from apps.audit.models import AuditEvent

audit_logger = logging.getLogger("apps.audit")


def get_client_ip(request):
    """Extract the client IP address from a Django request.

    Honours the ``X-Forwarded-For`` header when a reverse proxy is present
    (common behind Nginx/Gunicorn or Render's edge).  Falls back to
    ``REMOTE_ADDR``.
    """
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_event(
    *,
    category,
    action,
    user=None,
    target_content_type="",
    target_object_id=None,
    ip_address=None,
    extra=None,
):
    """Create an ``AuditEvent`` record.

    Parameters
    ----------
    category : str
        One of the ``AuditEvent.Category`` values.
    action : str
        Human-readable description of what happened.
    user : User or None
        The user who performed the action.  Values that are not real,
        persisted ``User`` instances (e.g. Django's ``AnonymousUser``, or an
        unsaved instance) are treated as no user and stored as ``NULL``.
    target_content_type : str
        Optional dotted ``app_label.Model`` of the target object.
    target_object_id : int or None
        Optional PK of the target object.
    ip_address : str or None
        Client IP address.
    extra : dict or None
        Arbitrary additional context.
    """
    actor = None
    if user is not None and getattr(user, "pk", None) is not None:
        actor = user
    event = AuditEvent.objects.create(
        user=actor,
        category=category,
        action=action,
        target_content_type=target_content_type,
        target_object_id=target_object_id,
        ip_address=ip_address,
        extra=extra or {},
    )
    audit_logger.info(
        "AuditEvent [%s] %s (user=%s, target=%s/%s)",
        category,
        action,
        user_id_or_system(actor),
        target_content_type or "-",
        target_object_id or "-",
    )
    return event


def log_auth_event(*, action, user=None, ip_address=None, extra=None):
    """Convenience wrapper for authentication-related audit events."""
    return log_event(
        category=AuditEvent.Category.AUTH,
        action=action,
        user=user,
        ip_address=ip_address,
        extra=extra,
    )


def log_admin_event(
    *,
    action,
    user=None,
    target_content_type="",
    target_object_id=None,
    ip_address=None,
    extra=None,
):
    """Convenience wrapper for administrative audit events."""
    return log_event(
        category=AuditEvent.Category.ADMIN,
        action=action,
        user=user,
        target_content_type=target_content_type,
        target_object_id=target_object_id,
        ip_address=ip_address,
        extra=extra,
    )


def log_data_event(
    *,
    action,
    user=None,
    target_content_type="",
    target_object_id=None,
    ip_address=None,
    extra=None,
):
    """Convenience wrapper for data-integrity audit events."""
    return log_event(
        category=AuditEvent.Category.DATA,
        action=action,
        user=user,
        target_content_type=target_content_type,
        target_object_id=target_object_id,
        ip_address=ip_address,
        extra=extra,
    )


def log_system_event(*, action, extra=None):
    """Convenience wrapper for system-generated audit events."""
    return log_event(
        category=AuditEvent.Category.SYSTEM,
        action=action,
        extra=extra,
    )


def user_id_or_system(user):
    """Return the user's PK or the string ``'system'``."""
    return getattr(user, "pk", None) or "system"
