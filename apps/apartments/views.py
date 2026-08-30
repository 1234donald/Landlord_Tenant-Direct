"""Views for the Apartment module (Phase 3, Sprint 3.4).

Implements apartment creation: ``POST /api/v1/apartments/``. The endpoint is
restricted to the LANDLORD role and always assigns the apartment to the
authenticated landlord (ownership is never client-supplied). Uploaded images
are validated before storage (AGENTS 24).
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsLandlord

from .models import Apartment, ApartmentImage
from .serializers import (
    ApartmentCreateSerializer,
    ApartmentImageRequestSerializer,
    ApartmentSerializer,
)


def _get_images(request):
    """Return uploaded image files (possibly empty) from a multipart request."""
    return request.FILES.getlist("images")


class ApartmentCreateView(APIView):
    """Create an apartment listing owned by the authenticated landlord."""

    permission_classes = [IsLandlord]

    def post(self, request):
        serializer = ApartmentCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Apartment creation failed.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        images = _get_images(request)
        if len(images) > 10:
            return Response(
                {
                    "success": False,
                    "message": "Apartment creation failed.",
                    "errors": {"images": "At most 10 images are allowed."},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate every image before persisting anything so an invalid upload
        # never leaves a partial listing behind.
        validator = ApartmentImageRequestSerializer()
        image_errors = []
        for image in images:
            try:
                validator.validate_image_file(image)
            except Exception as exc:
                image_errors.append(str(exc.detail) if hasattr(exc, "detail") else str(exc))

        if image_errors:
            return Response(
                {
                    "success": False,
                    "message": "Apartment creation failed.",
                    "errors": {"images": image_errors},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        apartment = Apartment.objects.create(**serializer.validated_data)
        for order, image_file in enumerate(images):
            ApartmentImage.objects.create(
                apartment=apartment,
                image=image_file,
                order=order,
            )

        return Response(
            {
                "success": True,
                "message": "Apartment created.",
                "data": ApartmentSerializer(apartment).data,
            },
            status=status.HTTP_201_CREATED,
        )
