"""Landlord verification data model (Phase 3, Sprint 3.1).

The ``VerificationRequest`` model represents a landlord's verification
submission within the administrative review workflow. It is an administrative
platform control only: it does NOT claim to legally verify property ownership,
verify land title, verify government documents or make legal determinations
(AGENTS 9, 17).
"""
from django.conf import settings
from django.db import models
from django.utils import timezone


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

    def approve(self, admin):
        """Approve this request as an administrative review action.

        Only a request still in the PENDING state can be approved. Records the
        reviewing administrator and the review timestamp.
        """
        if not self.is_pending:
            raise ValueError("Only pending requests can be approved.")
        self.status = self.Status.APPROVED
        self.reviewed_by = admin
        self.reviewed_at = timezone.now()
        self.save(
            update_fields=["status", "reviewed_by", "reviewed_at", "updated_at"]
        )

    def reject(self, admin, remarks=""):
        """Reject this request as an administrative review action.

        Only a request still in the PENDING state can be rejected. Records the
        reviewing administrator, the review timestamp and any remarks.
        """
        if not self.is_pending:
            raise ValueError("Only pending requests can be rejected.")
        self.status = self.Status.REJECTED
        self.reviewed_by = admin
        self.reviewed_at = timezone.now()
        self.remarks = remarks or ""
        self.save(
            update_fields=[
                "status",
                "reviewed_by",
                "reviewed_at",
                "remarks",
                "updated_at",
            ]
        )
