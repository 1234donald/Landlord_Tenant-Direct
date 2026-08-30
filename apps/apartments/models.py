"""Apartment listing data model (Phase 3, Sprint 3.3).

The ``Apartment`` model represents a landlord's residential apartment listing.
It carries the structured attributes used for search/filtering and, later, as
the candidate feature vectors for the Weighted KNN recommendation component
(AGENTS 10, 13). Facility availability (parking, electricity, water, security)
and furnishing status are modelled as boolean attributes so they can be used as
feature values. An optional free-text field captures any additional facilities
not covered by the standard flags.
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Apartment(models.Model):
    """A residential apartment listing owned by a LANDLORD user.

    Relationships:
        - ``landlord`` (required): the LANDLORD user who manages the listing.
    """

    class ApartmentType(models.TextChoices):
        SELF_CONTAINED = "SELF_CONTAINED", "Self-contained"
        ONE_BEDROOM = "ONE_BEDROOM", "One-bedroom"
        TWO_BEDROOM = "TWO_BEDROOM", "Two-bedroom"
        THREE_BEDROOM = "THREE_BEDROOM", "Three-bedroom"
        FLAT = "FLAT", "Flat"
        DUPLEX = "DUPLEX", "Duplex"

    landlord = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="apartments",
        limit_choices_to={"role": "LANDLORD"},
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200)
    address = models.CharField(
        max_length=300,
        blank=True,
        help_text="Address or area details.",
    )
    rental_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Rental price in the base currency.",
    )
    apartment_type = models.CharField(
        max_length=20,
        choices=ApartmentType.choices,
    )
    bedrooms = models.PositiveIntegerField()
    bathrooms = models.PositiveIntegerField()

    parking = models.BooleanField(
        default=False,
        help_text="Parking is available.",
    )
    electricity = models.BooleanField(
        default=False,
        help_text="Electricity supply is available.",
    )
    water = models.BooleanField(
        default=False,
        help_text="Water supply is available.",
    )
    security = models.BooleanField(
        default=False,
        help_text="Security is available.",
    )
    furnished = models.BooleanField(
        default=False,
        help_text="The apartment is furnished.",
    )
    additional_facilities = models.CharField(
        max_length=500,
        blank=True,
        help_text="Any additional facilities not covered by the standard flags.",
    )

    availability = models.BooleanField(
        default=True,
        help_text="Whether the apartment is currently available for rent.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["location"]),
            models.Index(fields=["rental_price"]),
            models.Index(fields=["apartment_type"]),
            models.Index(fields=["landlord"]),
            models.Index(fields=["availability"]),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        """Validate apartment attributes before saving.

        Rental price must be numeric and positive, and bedroom/bathroom counts
        must be valid non-negative values (AGENTS 10).
        """
        super().clean()
        errors = {}

        if self.rental_price is not None and self.rental_price < 0:
            errors["rental_price"] = "Rental price must be a positive number."

        if self.bedrooms is not None and self.bedrooms <= 0:
            errors["bedrooms"] = "Bedroom count must be at least 1."

        if self.bathrooms is not None and self.bathrooms <= 0:
            errors["bathrooms"] = "Bathroom count must be at least 1."

        if errors:
            raise ValidationError(errors)
