"""HTML presentation views for the Apartment module (Phase 3, Sprint 3.6; Phase
4, Sprints 4.1-4.2).

These form the read-oriented presentation layer (AGENTS 6): a public apartment
browsing page rendered as apartment cards, a full apartment detail page showing
facilities, availability and landlord information, and a landlord-only page
listing a landlord's own apartments. They are separate from the REST API views
in ``apps.apartments.views``.
"""
from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import DetailView, ListView

from .models import Apartment, ApartmentImage
from .serializers import ApartmentImageRequestSerializer, validate_video_file
from .views import build_search_queryset


class LandlordOnlyMixin:
    """Restrict a view to authenticated LANDLORD users (AGENTS 8).

    Administrators are also permitted so the console can manage listings, but
    tenants and anonymous users are blocked with a 403.
    """

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not (user and user.is_authenticated):
            return HttpResponseForbidden("Forbidden")
        if not (user.is_landlord or user.is_admin):
            return HttpResponseForbidden("Forbidden")
        return super().dispatch(request, *args, **kwargs)


class ApartmentForm(forms.ModelForm):
    """Create/update form mirroring the API ``_ApartmentBaseSerializer``.

    Server-side validation is identical to the API: rental price must be
    positive and bedroom/bathroom counts must be at least 1 (AGENTS 10, 23).
    """

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
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 4}
            ),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "rental_price": forms.NumberInput(attrs={"class": "form-control", "min": "0", "step": "0.01"}),
            "apartment_type": forms.Select(attrs={"class": "form-select"}),
            "bedrooms": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "bathrooms": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "additional_facilities": forms.TextInput(attrs={"class": "form-control"}),
            "video": forms.ClearableFileInput(
                attrs={"class": "form-control", "accept": ".mp4,.webm,.mov"}
            ),
        }

    def clean_rental_price(self):
        value = self.cleaned_data["rental_price"]
        if value is not None and value < 0:
            raise forms.ValidationError("Rental price must be a positive number.")
        return value

    def clean_bedrooms(self):
        value = self.cleaned_data["bedrooms"]
        if value is not None and value <= 0:
            raise forms.ValidationError("Bedroom count must be at least 1.")
        return value

    def clean_bathrooms(self):
        value = self.cleaned_data["bathrooms"]
        if value is not None and value <= 0:
            raise forms.ValidationError("Bathroom count must be at least 1.")
        return value

    def clean_video(self):
        video = self.cleaned_data.get("video")
        if not video:
            return video
        try:
            return validate_video_file(video)
        except Exception as exc:
            message = str(exc.detail) if hasattr(exc, "detail") else str(exc)
            raise forms.ValidationError(message)


def _get_managed_apartment(request, pk):
    """Fetch an apartment the current user is allowed to manage (AGENTS 8).

    Only the owning landlord or an administrator may manage a listing; any
    other user gets a 403. Raises 404 when the listing does not exist.
    """
    apartment = get_object_or_404(Apartment, pk=pk)
    if not (request.user.is_admin or apartment.landlord_id == request.user.id):
        raise PermissionDenied
    return apartment


def _store_images(apartment, files):
    """Validate and attach uploaded images to an apartment (AGENTS 24).

    Each image is validated for type, integrity and size and then stored as an
    ``ApartmentImage`` row. Invalid files are skipped; a file that is not a
    genuine image is never stored.
    """
    validator = ApartmentImageRequestSerializer()
    for order, file_obj in enumerate(files):
        try:
            validator.validate_image_file(file_obj)
        except forms.ValidationError:
            continue
        ApartmentImage.objects.create(
            apartment=apartment, image=file_obj, order=order
        )


class ApartmentBrowseView(ListView):
    """Public list of available apartments rendered as cards.

    Supports the Sprint 4.1-4.2 combined search/filter criteria supplied
    through the query string (location, apartment type, price range, bedrooms,
    bathrooms and facility flags). Only apartments currently available
    (``availability=True``) are shown so a listing that is unavailable is not
    presented to prospective tenants. A ``sort`` query parameter allows
    price-based sorting (``price_asc`` / ``price_desc`` / ``newest`` / ``oldest``).
    """

    template_name = "apartments/list.html"
    context_object_name = "apartments"
    paginate_by = 12

    def get_queryset(self):
        try:
            queryset = build_search_queryset(self.request.GET)
        except ValueError:
            # A malformed search should not break browsing; fall back to all
            # available listings.
            queryset = Apartment.objects.all()
        queryset = queryset.filter(availability=True).prefetch_related("images")

        sort = self.request.GET.get("sort")
        if sort == "price_asc":
            queryset = queryset.order_by("rental_price")
        elif sort == "price_desc":
            queryset = queryset.order_by("-rental_price")
        elif sort == "oldest":
            queryset = queryset.order_by("created_at")
        else:
            queryset = queryset.order_by("updated_at")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["apartment_types"] = Apartment.ApartmentType.choices
        labels = {
            "parking": "Parking",
            "electricity": "Electricity",
            "water": "Water",
            "security": "Security",
            "furnished": "Furnished",
        }
        context["facility_fields"] = [
            {
                "name": name,
                "label": label,
                "checked": bool(self.request.GET.get(name)),
            }
            for name, label in labels.items()
        ]
        # Preserve every other filter when the sort control or pagination is
        # changed.
        context["query_without_sort"] = self.request.GET.copy()
        context["query_without_sort"].pop("sort", None)
        context["query_without_sort"].pop("page", None)
        context["current_sort"] = self.request.GET.get("sort")
        context["is_paginated"] = context.get("is_paginated", False)
        return context


class ApartmentDetailPageView(DetailView):
    """Full presentation of a single apartment listing.

    Shows the structured listing data: price, type, bedrooms/bathrooms,
    facilities, availability and the landlord's permitted information, plus the
    uploaded media gallery. Also exposes the landlord's latest verification
    status (when present) so the page can display an appropriate badge.
    """

    model = Apartment
    template_name = "apartments/detail.html"
    context_object_name = "apartment"

    def get_queryset(self):
        return Apartment.objects.prefetch_related("images").select_related(
            "landlord"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        apartment = self.object
        latest_verification = (
            apartment.landlord.verification_requests.order_by("-submitted_at").first()
            if hasattr(apartment.landlord, "verification_requests")
            else None
        )
        context["landlord_verification"] = latest_verification
        return context


class MyApartmentsView(LoginRequiredMixin, ListView):
    """Landlord-only list of the authenticated landlord's own apartments.

    This provides the presentation side of apartment management (edit/delete are
    performed through the API). Only the owning landlord (or an administrator)
    can see this page.
    """

    template_name = "apartments/my_listings.html"
    context_object_name = "apartments"

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated and not (user.is_landlord or user.is_admin):
            # A tenant must not access landlord management pages.
            from django.http import HttpResponseForbidden

            return HttpResponseForbidden("Forbidden")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if self.request.user.is_admin:
            return Apartment.objects.all().prefetch_related("images")
        return self.request.user.apartments.prefetch_related("images")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_admin_view"] = self.request.user.is_admin
        return context


class ApartmentCreateView(LoginRequiredMixin, LandlordOnlyMixin, View):
    """Landlord-only page for creating a new apartment listing.

    The current landlord is always the owner; ownership is never client
    supplied (mirrors the API ``ApartmentCreateSerializer``).
    """

    template_name = "apartments/form.html"

    def get(self, request):
        form = ApartmentForm()
        return render(request, self.template_name, {"form": form, "is_edit": False})

    def post(self, request):
        form = ApartmentForm(request.POST, request.FILES)
        if form.is_valid():
            apartment = form.save(commit=False)
            apartment.landlord = request.user
            apartment.full_clean()
            apartment.save()
            _store_images(apartment, request.FILES.getlist("images"))
            messages.success(request, "Your apartment listing was created.")
            return redirect("my-apartments")
        return render(
            request,
            self.template_name,
            {"form": form, "is_edit": False},
            status=400,
        )


class ApartmentEditView(LoginRequiredMixin, LandlordOnlyMixin, View):
    """Landlord-only page for editing one of the landlord's own listings.

    Only the owning landlord (or an administrator) may edit a listing.
    """

    template_name = "apartments/form.html"

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        return response

    def get_apartment(self, request, pk):
        return _get_managed_apartment(request, pk)

    def get(self, request, pk):
        apartment = self.get_apartment(request, pk)
        form = ApartmentForm(instance=apartment)
        return render(
            request,
            self.template_name,
            {"form": form, "apartment": apartment, "is_edit": True},
        )

    def post(self, request, pk):
        apartment = self.get_apartment(request, pk)
        form = ApartmentForm(request.POST, request.FILES, instance=apartment)
        if form.is_valid():
            instance = form.save()
            _store_images(instance, request.FILES.getlist("images"))
            messages.success(request, "Your apartment listing was updated.")
            return redirect("my-apartments")
        return render(
            request,
            self.template_name,
            {"form": form, "apartment": apartment, "is_edit": True},
            status=400,
        )


class ApartmentDeleteView(LoginRequiredMixin, LandlordOnlyMixin, View):
    """Landlord-only action for deleting one of the landlord's own listings.

    POST-only; the listing is removed together with its uploaded images
    (database cascade). Only the owning landlord or an administrator may delete
    a listing (AGENTS 8); other routes that manage listings use this same check.
    """

    def post(self, request, pk):
        apartment = _get_managed_apartment(request, pk)
        apartment.delete()
        messages.success(request, "Your apartment listing was deleted.")
        return redirect("my-apartments")
