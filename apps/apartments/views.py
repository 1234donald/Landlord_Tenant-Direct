"""Views for the Apartment module (Phase 3, Sprints 3.4 and 3.5).

Implements apartment creation (``POST /api/v1/apartments/``, landlord-only) and
apartment management (``PATCH``/``DELETE /api/v1/apartments/{id}/``, owner or
admin). Ownership is always the authenticated landlord and is never
client-supplied; only the owning landlord or an administrator may modify or
delete a listing. Uploaded images are validated before storage (AGENTS 24).
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from apps.accounts.permissions import IsLandlord

from .models import Apartment, ApartmentImage
from .permissions import IsApartmentOwnerOrAdmin
from .serializers import (
    ApartmentCreateSerializer,
    ApartmentImageRequestSerializer,
    ApartmentSerializer,
    ApartmentUpdateSerializer,
)


def _get_images(request):
    """Return uploaded image files (possibly empty) from a multipart request."""
    return request.FILES.getlist("images")


def _validate_images(images):
    """Validate a list of uploaded image files, returning a list of errors.

    Returns an empty list when every image is valid. The caller must not
    persist anything until all images pass validation.
    """
    validator = ApartmentImageRequestSerializer()
    errors = []
    for image in images:
        try:
            validator.validate_image_file(image)
        except Exception as exc:
            message = str(exc.detail) if hasattr(exc, "detail") else str(exc)
            errors.append(message)
    return errors


def _replace_images(apartment, images):
    """Replace an apartment's image set with the given (validated) files.

    New images are created first and the old set removed only after the new
    uploads succeed, so a storage failure never leaves a listing without media.
    """
    created = []
    for order, image_file in enumerate(images):
        created.append(
            ApartmentImage.objects.create(
                apartment=apartment,
                image=image_file,
                order=order,
            )
        )
    apartment.images.exclude(pk__in=[img.pk for img in created]).delete()


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

        image_errors = _validate_images(images)
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


class ApartmentDetailView(APIView):
    """Update or delete a single apartment listing.

    Access is restricted to the owning landlord or an administrator
    (``IsApartmentOwnerOrAdmin``).
    """

    permission_classes = [IsApartmentOwnerOrAdmin]

    def _get_owned_apartment(self, request, pk):
        apartment = get_object_or_404(Apartment, pk=pk)
        self.check_object_permissions(request, apartment)
        return apartment

    def patch(self, request, pk):
        apartment = self._get_owned_apartment(request, pk)
        serializer = ApartmentUpdateSerializer(
            apartment,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Apartment update failed.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        images = _get_images(request)
        if len(images) > 10:
            return Response(
                {
                    "success": False,
                    "message": "Apartment update failed.",
                    "errors": {"images": "At most 10 images are allowed."},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        image_errors = _validate_images(images)
        if image_errors:
            return Response(
                {
                    "success": False,
                    "message": "Apartment update failed.",
                    "errors": {"images": image_errors},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer.save()
        if images:
            _replace_images(apartment, images)

        return Response(
            {
                "success": True,
                "message": "Apartment updated.",
                "data": ApartmentSerializer(apartment).data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        apartment = self._get_owned_apartment(request, pk)
        apartment.delete()
        return Response(
            {
                "success": True,
                "message": "Apartment deleted.",
                "data": {},
            },
            status=status.HTTP_200_OK,
        )
