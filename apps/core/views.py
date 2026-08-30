from django.shortcuts import render
from django.views.generic import TemplateView


class HomeView(TemplateView):
    """Home page for the platform foundation."""

    template_name = "home.html"


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
