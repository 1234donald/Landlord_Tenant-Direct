"""Tenant Preference and Recommendation data models (Phases 4-5).

The ``Preference`` model (Sprint 4.3) persists a tenant's apartment preferences.
It is the "Tenant Preference" entity (AGENTS 18, SYSTEM_REQUIREMENTS 7, 26) and
carries the structured attributes that form the query vector ``U = (u1, ..., un)``
for the Weighted KNN recommendation component (AGENTS 12). Each preference
belongs to a TENANT user (mirroring the ``Apartment.landlord`` relationship).

The ``Recommendation`` / ``RecommendationItem`` models (Sprint 5.6) persist a
Weighted KNN recommendation run, fulfilling the ``Recommendation`` entity and the
``Tenant ─── Recommendation ─── Apartment`` relationship (SYSTEM_REQUIREMENTS 25,
26). Facility preferences (parking, electricity, water, security, furnished) are
modelled as nullable booleans so that a tenant can express three states: the
facility is required (True), the facility is not required (False), or there is
no preference on that facility (None). Numerical and text preferences are
nullable/blank to leave the corresponding feature unconstrained when the tenant
has not expressed a preference.
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.apartments.models import Apartment
from ml.features import DEFAULT_K as ml_features_DEFAULT_K


class Preference(models.Model):
    """A tenant's stated apartment preferences.

    Relationships:
        - ``tenant`` (required): the TENANT user who owns the preference.
    """

    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="preferences",
        limit_choices_to={"role": "TENANT"},
        help_text="The tenant who owns this preference.",
    )
    location = models.CharField(
        max_length=200,
        blank=True,
        help_text="Preferred location.",
    )
    max_rent = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum rental price the tenant is willing to pay.",
    )
    apartment_type = models.CharField(
        max_length=20,
        choices=Apartment.ApartmentType.choices,
        null=True,
        blank=True,
        help_text="Preferred apartment type.",
    )
    bedrooms = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Preferred number of bedrooms.",
    )
    bathrooms = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Preferred number of bathrooms.",
    )

    parking = models.BooleanField(
        null=True,
        blank=True,
        help_text="Parking is required.",
    )
    electricity = models.BooleanField(
        null=True,
        blank=True,
        help_text="Electricity supply is required.",
    )
    water = models.BooleanField(
        null=True,
        blank=True,
        help_text="Water supply is required.",
    )
    security = models.BooleanField(
        null=True,
        blank=True,
        help_text="Security is required.",
    )
    furnished = models.BooleanField(
        null=True,
        blank=True,
        help_text="A furnished apartment is required.",
    )
    additional_facilities = models.CharField(
        max_length=500,
        blank=True,
        help_text="Any additional facilities the tenant requires.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant"]),
            models.Index(fields=["location"]),
            models.Index(fields=["max_rent"]),
            models.Index(fields=["apartment_type"]),
        ]

    def __str__(self):
        return f"Preference for {self.tenant_id} ({self.pk})"

    def clean(self):
        """Validate preference values before saving.

        The maximum rental price must be numeric and positive, and bedroom and
        bathroom counts must be valid non-negative values where provided
        (AGENTS 23).
        """
        super().clean()
        errors = {}

        if self.max_rent is not None and self.max_rent < 0:
            errors["max_rent"] = "Maximum rental price must be a positive number."

        if self.bedrooms is not None and self.bedrooms <= 0:
            errors["bedrooms"] = "Bedroom count must be at least 1."

        if self.bathrooms is not None and self.bathrooms <= 0:
            errors["bathrooms"] = "Bathroom count must be at least 1."

        if errors:
            raise ValidationError(errors)


class Recommendation(models.Model):
    """A persisted Weighted KNN recommendation run for a TENANT.

    Fulfils the ``Recommendation`` entity (SYSTEM_REQUIREMENTS 25, 26) and the
    ``Tenant ─── Recommendation ─── Apartment`` relationship. Each run captures
    the tenant, the stored preference that produced it, the algorithm used and
    the configured K, and links to its ranked ``RecommendationItem`` rows.
    """

    class Algorithm(models.TextChoices):
        WEIGHTED_KNN = "weighted_knn", "Weighted KNN"

    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recommendations",
        limit_choices_to={"role": "TENANT"},
        help_text="The tenant who owns this recommendation run.",
    )
    preference = models.ForeignKey(
        Preference,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recommendations",
        help_text="The preference that generated this recommendation run.",
    )
    algorithm = models.CharField(
        max_length=20,
        choices=Algorithm.choices,
        default=Algorithm.WEIGHTED_KNN,
    )
    k = models.PositiveIntegerField(
        default=ml_features_DEFAULT_K,
        help_text="Number of nearest neighbours used for this run.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant"]),
            models.Index(fields=["preference"]),
        ]

    def __str__(self):
        return f"Recommendation for tenant {self.tenant_id} ({self.pk})"


class RecommendationItem(models.Model):
    """One ranked apartment within a ``Recommendation`` run.

    Records the apartment recommended, its 1-based ranking position, and the
    weighted distance/similarity produced by the Weighted KNN engine.
    """

    recommendation = models.ForeignKey(
        Recommendation,
        on_delete=models.CASCADE,
        related_name="items",
    )
    apartment = models.ForeignKey(
        Apartment,
        on_delete=models.CASCADE,
        related_name="recommendation_items",
    )
    rank = models.PositiveIntegerField(
        help_text="1-based ranking position (lowest distance = rank 1).",
    )
    distance = models.FloatField(
        help_text="Weighted Euclidean distance from the tenant query vector.",
    )
    similarity = models.FloatField(
        help_text="Bounded preference-match score derived from the distance.",
    )

    class Meta:
        ordering = ["recommendation", "rank"]
        constraints = [
            models.UniqueConstraint(
                fields=["recommendation", "apartment"],
                name="unique_recommendation_apartment",
            ),
        ]
        indexes = [
            models.Index(fields=["recommendation", "rank"]),
        ]

    def __str__(self):
        return f"Rank {self.rank} for recommendation {self.recommendation_id}"
