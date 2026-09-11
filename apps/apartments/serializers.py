"""Serializers for the Apartment module (Phase 3, Sprint 3.4).

These support apartment creation (landlord-only) including validated image
uploads. Image uploads are validated for type, integrity and size before being
stored (AGENTS 24, SYSTEM_REQUIREMENTS 27).
"""
from PIL import Image
from rest_framework import serializers

from .models import Apartment, ApartmentImage

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50 MB


def validate_video_file(file_obj):
    """Validate a single uploaded apartment video file (AGENTS 24).

    Checks file type by extension, size and container signature (magic bytes)
    so an arbitrary or executable payload is never stored as a video.
    ``is_valid_apartment_video`` is used by the serializer and the presentation
    form so both layers enforce exactly the same rules.
    """
    if file_obj is None:
        raise serializers.ValidationError("A video file is required.")
    if file_obj.size > MAX_VIDEO_SIZE:
        raise serializers.ValidationError(
            f"Video file must be {MAX_VIDEO_SIZE // (1024 * 1024)} MB or "
            "smaller."
        )
    name = (file_obj.name or "").lower()
    allowed = {".mp4", ".webm", ".mov"}
    if name and not any(name.endswith(ext) for ext in allowed):
        raise serializers.ValidationError(
            "Unsupported video type. Allowed extensions are: "
            + ", ".join(sorted(allowed))
        )
    signature = file_obj.read(12)
    file_obj.seek(0)
    # MP4/MOV: bytes 4-7 hold the "ftyp" brand. WebM: EBML magic 0x1A45DFA3.
    is_mp4 = signature[4:8] == b"ftyp"
    is_webm = signature[0:4] == b"\x1a\x45\xdf\xa3"
    if not (is_mp4 or is_webm):
        raise serializers.ValidationError(
            "The uploaded file is not a supported video container."
        )
    return file_obj


class _ApartmentBaseSerializer(serializers.ModelSerializer):
    """Shared apartment field set used by the create/write serializers."""

    class Meta:
        model = Apartment
        fields = [
            "title",
            "description",
            "location",
            "address",
            "rental_price",
            "apartment_type",
            "bedrooms",
            "bathrooms",
            "parking",
            "electricity",
            "water",
            "security",
            "furnished",
            "additional_facilities",
            "availability",
            "video",
        ]
        extra_kwargs = {
            "description": {"required": False},
            "address": {"required": False},
            "parking": {"required": False},
            "electricity": {"required": False},
            "water": {"required": False},
            "security": {"required": False},
            "furnished": {"required": False},
            "additional_facilities": {"required": False},
            "availability": {"required": False},
            "video": {"required": False, "allow_null": True},
        }

    def validate_rental_price(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError(
                "Rental price must be a positive number."
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

    def validate_video(self, value):
        if value is None:
            return value
        return validate_video_file(value)


class ApartmentImageRequestSerializer(serializers.Serializer):
    """Validation for a single uploaded apartment image file.

    Validates the file type, integrity and size. Pillow is used to confirm the
    uploaded content is a real image and is not an executable or arbitrary
    payload disguised as an image (AGENTS 24).
    """

    def validate_image_file(self, file_obj):
        if file_obj is None:
            raise serializers.ValidationError("An image file is required.")
        if file_obj.size > MAX_IMAGE_SIZE:
            raise serializers.ValidationError(
                f"Image file must be {MAX_IMAGE_SIZE // (1024 * 1024)} MB or "
                "smaller."
            )
        name = (file_obj.name or "").lower()
        allowed = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
        if name and not any(name.endswith(ext) for ext in allowed):
            raise serializers.ValidationError(
                "Unsupported image type. Allowed extensions are: "
                + ", ".join(sorted(allowed))
            )
        try:
            with Image.open(file_obj) as image:
                image.verify()
        except Exception:
            raise serializers.ValidationError(
                "The uploaded file is not a valid image."
            )
        file_obj.seek(0)
        return file_obj


class ApartmentCreateSerializer(_ApartmentBaseSerializer):
    """Create an apartment listing.

    The owning landlord is taken from the authenticated request and is never
    accepted from the client. Image files are validated and attached by the
    view (see ``ApartmentListCreateView``).
    """

    def validate(self, attrs):
        # Ownership is always the authenticated landlord; never client-supplied.
        attrs["landlord"] = self.context["request"].user
        return attrs


class ApartmentUpdateSerializer(_ApartmentBaseSerializer):
    """Partial update of an apartment listing.

    Only the supplied fields are updated (partial). Listing ownership is never
    editable through this endpoint. Image replacement is handled by the view
    (see ``ApartmentDetailView``).
    """


class ApartmentImageSerializer(serializers.ModelSerializer):
    """Read representation of an apartment image."""

    class Meta:
        model = ApartmentImage
        fields = ["id", "image", "order", "uploaded_at"]
        read_only_fields = fields


class ApartmentSerializer(serializers.ModelSerializer):
    """Read representation of an apartment listing with its images."""

    images = ApartmentImageSerializer(many=True, read_only=True)
    landlord_email = serializers.EmailField(
        source="landlord.email", read_only=True
    )

    class Meta:
        model = Apartment
        fields = [
            "id",
            "landlord",
            "landlord_email",
            "title",
            "description",
            "location",
            "address",
            "rental_price",
            "apartment_type",
            "bedrooms",
            "bathrooms",
            "parking",
            "electricity",
            "water",
            "security",
            "furnished",
            "additional_facilities",
            "availability",
            "video",
            "images",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
