"""Audit event data model (Phase 6, Sprint 6.5).

The ``AuditEvent`` model records significant administrative and security
events for operational visibility. It provides an append-only audit trail
covering:

- authentication events (login, logout, failed login);
- administrative actions (user status change, apartment moderation,
  verification approve/reject);
- data-integrity events (model deletion, constraint violation).

Every event captures the acting user (if available), the event category, a
human-readable action description, the optional target object type and ID,
the client IP address, and a UTC timestamp.

The model is intentionally append-only: no update or delete methods are
provided at the application level. Database-level protection (constraints)
is added where the database engine supports it.
"""
from django.conf import settings
from django.db import models


class AuditEvent(models.Model):
    """An immutable audit record of a significant system event.

    Relationships:
        - ``user`` (optional): the user who performed the action.  May be
          ``NULL`` for system-generated or anonymous events (e.g. a failed
          login where the user could not be identified).
    """

    class Category(models.TextChoices):
        AUTH = "AUTH", "Authentication"
        ADMIN = "ADMIN", "Administrative Action"
        DATA = "DATA", "Data Integrity"
        SYSTEM = "SYSTEM", "System Event"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
        help_text="The user who performed this action (may be NULL for system events).",
    )
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        help_text="High-level event category.",
    )
    action = models.CharField(
        max_length=255,
        help_text="Human-readable description of the event.",
    )
    target_content_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="Django content type of the target object (e.g. 'accounts.User').",
    )
    target_object_id = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        help_text="Primary key of the target object, if any.",
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="Client IP address at the time of the event.",
    )
    extra = models.JSONField(
        default=dict,
        blank=True,
        help_text="Arbitrary JSON payload for additional context.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category"]),
            models.Index(fields=["user"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["target_content_type", "target_object_id"]),
        ]

    def __str__(self):
        user_label = self.user_id or "system"
        return f"[{self.category}] {self.action} (user={user_label}, {self.created_at})"
