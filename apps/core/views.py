from django.http import HttpResponse
from django.views.generic import TemplateView


class HomeView(TemplateView):
    """Simple home page for the platform foundation."""

    template_name = "home.html"
