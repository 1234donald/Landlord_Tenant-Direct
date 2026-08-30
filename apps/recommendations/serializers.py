"""Serializers for the Tenant Preference module (Phase 4, Sprint 4.4).

These support tenant-preference management (§24.3): create, retrieve, update
and validation of a tenant's apartment preferences. Preferences are owned by
the TENANT user and are never client-supplied; the owning tenant is always the
authenticated request user. All preference values are validated before they are
stored (AGENTS 23).

The read serializer exposes the stored preference exactly as it will be fed to
the recommendation component, and the write serializers validate each value so
that invalid data (e.g. a negative ``max_rent``) is never persisted.
"""
from rest_framework import serializers

from apps.apartments.models import Apartment
from apps.apartments.serializers import ApartmentSerializer

from .models import Preference, Recommendation, RecommendationItem


class PreferenceSerializer(serializers.ModelSerializer):
    """Read representation of a tenant preference."""

    tenant_email = serializers.EmailField(
        source="tenant.email", read_only=True
    )

    class Meta:
        model = Preference
        fields = [
            "id",
            "tenant",
            "tenant_email",
            "location",
            "max_rent",
            "apartment_type",
            "bedrooms",
            "bathrooms",
            "parking",
            "electricity",
            "water",
            "security",
            "furnished",
            "additional_facilities",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class _PreferenceBaseSerializer(serializers.ModelSerializer):
    """Shared write field set and validation for tenant preferences.

    Validation mirrors the model's ``clean()`` (AGENTS 23): ``max_rent`` must
    be a positive number and ``bedrooms``/``bathrooms`` must be at least 1 when
    provided.
    """

    class Meta:
        model = Preference
        fields = [
            "location",
            "max_rent",
            "apartment_type",
            "bedrooms",
            "bathrooms",
            "parking",
            "electricity",
            "water",
            "security",
            "furnished",
            "additional_facilities",
        ]
        extra_kwargs = {
            "location": {"required": False},
            "max_rent": {"required": False},
            "apartment_type": {"required": False},
            "bedrooms": {"required": False},
            "bathrooms": {"required": False},
            "parking": {"required": False},
            "electricity": {"required": False},
            "water": {"required": False},
            "security": {"required": False},
            "furnished": {"required": False},
            "additional_facilities": {"required": False},
        }

    def validate_apartment_type(self, value):
        if value is None:
            return value
        valid_types = {choice[0] for choice in Apartment.ApartmentType.choices}
        if value not in valid_types:
            raise serializers.ValidationError("Invalid apartment type.")
        return value

    def validate_max_rent(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError(
                "Maximum rental price must be a positive number."
            )
        return value

    def validate_bedrooms(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError(
                "Bedroom count must be at least 1."
            )
        return value

    def validate_bathrooms(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError(
                "Bathroom count must be at least 1."
            )
        return value


class PreferenceCreateSerializer(_PreferenceBaseSerializer):
    """Create a tenant preference owned by the authenticated tenant.

    Ownership is always the authenticated request user and is never accepted
    from the client.
    """

    def validate(self, attrs):
        attrs["tenant"] = self.context["request"].user
        return attrs


class PreferenceUpdateSerializer(_PreferenceBaseSerializer):
    """Partial update of a tenant preference.

    Only the supplied fields are updated. Ownership is never editable through
    this endpoint.
    """


class RecommendationItemSerializer(serializers.ModelSerializer):
    """Read representation of one ranked apartment within a recommendation run.

    Mirrors the recommendation API result shape (SYSTEM_REQUIREMENTS 24.4):
    ``apartment_id``, ``rank`` and ``distance``, plus the derived similarity
    score and the nested apartment data for presentation.
    """

    apartment = ApartmentSerializer(read_only=True)

    class Meta:
        model = RecommendationItem
        fields = [
            "id",
            "apartment",
            "rank",
            "distance",
            "similarity",
        ]
        read_only_fields = fields


class RecommendationSerializer(serializers.ModelSerializer):
    """Read representation of a persisted recommendation run."""

    items = RecommendationItemSerializer(many=True, read_only=True)
    preference_id = serializers.PrimaryKeyRelatedField(
        source="preference", read_only=True
    )

    class Meta:
        model = Recommendation
        fields = [
            "id",
            "tenant",
            "preference_id",
            "algorithm",
            "k",
            "created_at",
            "items",
        ]
        read_only_fields = fields
