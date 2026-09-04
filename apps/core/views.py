from django.shortcuts import render
from django.views.generic import TemplateView

from apps.apartments.models import Apartment
from apps.apartments.views import build_search_queryset


class HomeView(TemplateView):
    """Home page for the platform foundation.

    Passes featured (recently updated, available) apartments to the template so
    the homepage can show a "Featured listings" section, plus the apartment
    types for the primary search bar.
    """

    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        featured = (
            Apartment.objects.filter(availability=True)
            .prefetch_related("images")
            .order_by("-updated_at")[:6]
        )
        context["featured_apartments"] = featured
        context["apartment_types"] = Apartment.ApartmentType.choices
        context["total_available"] = Apartment.objects.filter(
            availability=True
        ).count()
        return context


class AboutView(TemplateView):
    """About page describing the project."""

    template_name = "about.html"


def handler400(request, exception=None, template_name="errors/400.html"):
    """Handle bad-request errors with a clean, non-leaking page."""
    return render(request, template_name, status=400)


def handler404(request, exception, template_name="errors/404.html"):
    """Handle not-found errors with a clean, non-leaking page.

    Renders a brand-consistent 404 page (Sprint 6.3 "secure error responses").
    It never echoes the requested path in a way that leaks internals and never
    exposes stack traces, credentials or internal paths (AGENTS 22).
    """
    return render(request, template_name, status=404)


def handler500(request, template_name="errors/500.html"):
    """Handle server errors with a clean, non-leaking page.

    With DEBUG=False Django never renders a traceback to users; this handler
    returns a simple, friendly 500 page instead. Errors are logged at the
    application level (AGENTS 22, 27).
    """
    return render(request, template_name, status=500)
