"""Landlord verification data model (Phase 3, Sprint 3.1).

The ``VerificationRequest`` model represents a landlord's verification
submission within the administrative review workflow. It is an administrative
platform control only: it does NOT claim to legally verify property ownership,
verify land title, verify government documents or make legal determinations
(AGENTS 9, 17).
"""
from django.conf import settings
from django.db import models


class VerificationRequest(models.Model):
    """A landlord's verification submission awaiting administrative review.

    Relationships:
        - ``landlord`` (required): the LANDLORD user being verified.
        - ``reviewed_by`` (optional): the ADMIN user who reviewed the request.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    landlord = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="verification_requests",
        limit_choices_to={"role": "LANDLORD"},
    )
    information = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    remarks = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verification_reviews",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-submitted_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["landlord"]),
        ]

    def __str__(self):
        return f"Verification for {self.landlord_id} ({self.status})"

    @property
    def is_pending(self):
        return self.status == self.Status.PENDING

    @property
    def is_approved(self):
        return self.status == self.Status.APPROVED

    @property
    def is_rejected(self):
        return self.status == self.Status.REJECTED
