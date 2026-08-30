"""HTML presentation views for the Apartment module (Phase 3, Sprint 3.6; Phase
4, Sprint 4.1).

These form the read-oriented presentation layer (AGENTS 6): a public apartment
browsing page rendered as apartment cards, a full apartment detail page showing
facilities, availability and landlord information, and a landlord-only page
listing a landlord's own apartments. They are separate from the REST API views
in ``apps.apartments.views``.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, ListView

from .models import Apartment
from .views import build_search_queryset


class ApartmentBrowseView(ListView):
    """Public list of available apartments rendered as cards.

    Supports the Sprint 4.1 basic search criteria supplied through the query
    string (location, apartment type, price, bedrooms, bathrooms). Only
    apartments currently available (``availability=True``) are shown so a
    listing that is unavailable is not presented to prospective tenants.
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
        return queryset.filter(availability=True).prefetch_related("images")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["apartment_types"] = Apartment.ApartmentType.choices
        return context


class ApartmentDetailPageView(DetailView):
    """Full presentation of a single apartment listing.

    Shows the structured listing data: price, type, bedrooms/bathrooms,
    facilities, availability and the landlord's permitted information, plus the
    uploaded media gallery.
    """

    model = Apartment
    template_name = "apartments/detail.html"
    context_object_name = "apartment"

    def get_queryset(self):
        return Apartment.objects.prefetch_related("images").select_related(
            "landlord"
        )


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
