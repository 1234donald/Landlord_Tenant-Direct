"""Serializers for the landlord verification workflow (Phase 3, Sprint 3.2).

These support the landlord submission/status endpoints and the administrative
review (list, approve, reject) endpoints defined in the Verification API
(§24.6).
"""
from rest_framework import serializers

from apps.verification.models import VerificationRequest


class VerificationRequestSerializer(serializers.ModelSerializer):
    """Read representation of a verification request."""

    landlord_email = serializers.EmailField(
        source="landlord.email", read_only=True
    )
    reviewed_by_email = serializers.EmailField(
        source="reviewed_by.email", read_only=True, allow_null=True
    )

    class Meta:
        model = VerificationRequest
        fields = [
            "id",
            "landlord",
            "landlord_email",
            "information",
            "status",
            "remarks",
            "submitted_at",
            "reviewed_by",
            "reviewed_by_email",
            "reviewed_at",
        ]
        read_only_fields = fields


class VerificationSubmitSerializer(serializers.Serializer):
    """Create a new landlord verification submission.

    The landlord is taken from the authenticated request. A new submission is
    rejected while the landlord already has a PENDING request.
    """

    information = serializers.CharField(trim_whitespace=False)

    def validate_information(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "Verification information cannot be blank."
            )
        if len(value) > 5000:
            raise serializers.ValidationError(
                "Verification information must be 5000 characters or fewer."
            )
        return value

    def validate(self, attrs):
        landlord = self.context["request"].user
        pending_exists = VerificationRequest.objects.filter(
            landlord=landlord,
            status=VerificationRequest.Status.PENDING,
        ).exists()
        if pending_exists:
            raise serializers.ValidationError(
                "You already have a pending verification request."
            )
        attrs["landlord"] = landlord
        return attrs

    def create(self, validated_data):
        return VerificationRequest.objects.create(
            landlord=validated_data["landlord"],
            information=validated_data["information"],
        )


class VerificationReviewSerializer(serializers.Serializer):
    """Validate the data accompanying an administrative review action."""

    remarks = serializers.CharField(
        required=False, allow_blank=True, max_length=2000
    )