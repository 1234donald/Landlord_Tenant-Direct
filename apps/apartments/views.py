"""Views for the Apartment module (Phase 3, Sprints 3.4-3.5; Phase 4, Sprint 4.2).

Implements apartment list/filter/search (``GET /api/v1/apartments/``), apartment
creation (``POST /api/v1/apartments/``, landlord-only) and apartment management
(``PATCH``/``DELETE /api/v1/apartments/{id}/``, owner or admin). Ownership is
always the authenticated landlord and is never client-supplied; only the owning
landlord or an administrator may modify or delete a listing. Uploaded images
are validated before storage (AGENTS 24).
"""
from decimal import Decimal, InvalidOperation

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


PAGE_SIZE = 12


def _get_images(request):
    """Return uploaded image files (possibly empty) from a multipart request."""
    return request.FILES.getlist("images")


def _parse_positive_int(name, value):
    """Parse a positive integer query value, raising ValueError when invalid."""
    if value is None:
        return
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a whole number.")
    if parsed < 0:
        raise ValueError(f"{name} must be a positive number.")
    return parsed


def _parse_price(name, value):
    """Parse a non-negative price query value, raising ValueError when invalid."""
    if value is None:
        return
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{name} must be a number.")
    if parsed < 0:
        raise ValueError(f"{name} must be a positive number.")
    return parsed


def _parse_bool(name, value):
    """Parse a boolean query value, raising ValueError when invalid.

    Accepts the common ``true/false``, ``1/0``, ``yes/no`` and ``on/off``
    spellings.
    """
    if value is None:
        return
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be true or false.")


# Boolean facility flags that can be used to filter listings.
FACILITY_FIELDS = ("parking", "electricity", "water", "security", "furnished")


def build_search_queryset(params):
    """Build an apartment queryset from the search/filter query parameters.

    Supports combined filtering (Sprints 4.1-4.2): location, apartment type,
    price range (minimum and maximum), bedroom/bathroom count, facility flags
    (parking, electricity, water, security, furnished) and availability. Raises
    ValueError with a mapping of field names to errors when parameters are
    invalid.
    """
    queryset = Apartment.objects.all().prefetch_related("images")
    errors = {}

    location = params.get("location")
    if location:
        queryset = queryset.filter(location__icontains=location.strip())

    apartment_type = params.get("apartment_type")
    if apartment_type:
        valid_types = {choice[0] for choice in Apartment.ApartmentType.choices}
        if apartment_type not in valid_types:
            errors["apartment_type"] = "Invalid apartment type."
        else:
            queryset = queryset.filter(apartment_type=apartment_type)

    try:
        min_price = _parse_price("min_price", params.get("min_price"))
        max_price = _parse_price("max_price", params.get("max_price"))
    except ValueError as exc:
        errors[exc.args[0].split(" ")[0]] = str(exc)
    else:
        if min_price is not None:
            queryset = queryset.filter(rental_price__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(rental_price__lte=max_price)

    try:
        bedrooms = _parse_positive_int("bedrooms", params.get("bedrooms"))
        bathrooms = _parse_positive_int("bathrooms", params.get("bathrooms"))
    except ValueError as exc:
        errors[exc.args[0].split(" ")[0]] = str(exc)
    else:
        if bedrooms is not None:
            queryset = queryset.filter(bedrooms=bedrooms)
        if bathrooms is not None:
            queryset = queryset.filter(bathrooms=bathrooms)

    try:
        for field in FACILITY_FIELDS:
            parsed = _parse_bool(field, params.get(field))
            if parsed is not None:
                queryset = queryset.filter(**{field: parsed})
        availability = _parse_bool("availability", params.get("availability"))
    except ValueError as exc:
        errors[exc.args[0].split(" ")[0]] = str(exc)
    else:
        if availability is not None:
            queryset = queryset.filter(availability=availability)

    if errors:
        raise ValueError(errors)

    return queryset


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


class ApartmentListCreateView(APIView):
    """List/search or create apartment listings.

    ``GET`` returns apartments matching the basic search criteria and is public
    (any visitor can browse). ``POST`` is restricted to the LANDLORD role and
    creates a listing owned by the authenticated landlord.
    """

    permission_classes = []

    def get_permissions(self):
        if self.request.method.upper() == "POST":
            return [IsLandlord()]
        return super().get_permissions()

    def get(self, request):
        try:
            queryset = build_search_queryset(request.query_params)
        except ValueError as exc:
            return Response(
                {
                    "success": False,
                    "message": "Apartment search failed.",
                    "errors": exc.args[0],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return self._paginated_response(request, queryset)

    def _paginated_response(self, request, queryset):
        """Paginate a queryset and return it with count/next/previous links.

        The ``page`` query parameter selects the page (default 1); page size is
        fixed by ``PAGE_SIZE``. ``data`` always holds the current page's items
        while ``count``, ``next`` and ``previous`` describe the overall result
        set.
        """
        try:
            page = int(request.query_params.get("page", 1))
        except (TypeError, ValueError):
            page = 1
        if page < 1:
            page = 1

        total = queryset.count()
        pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
        start = (page - 1) * PAGE_SIZE
        items = queryset[start : start + PAGE_SIZE]

        querystring = request.query_params.copy()
        querystring.pop("page", None)
        base = request.build_absolute_uri()

        def page_link(number):
            if number is None:
                return None
            params = querystring.copy()
            if number != 1:
                params["page"] = str(number)
            query = params.urlencode()
            return f"{base}?{query}" if query else base

        return Response(
            {
                "success": True,
                "message": "Apartments returned.",
                "count": total,
                "page": page,
                "pages": pages,
                "next": page_link(page + 1 if page < pages else None),
                "previous": page_link(page - 1 if page > 1 else None),
                "data": ApartmentSerializer(items, many=True).data,
            },
            status=status.HTTP_200_OK,
        )

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
