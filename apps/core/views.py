from django.views.generic import TemplateView


class HomeView(TemplateView):
    """Home page for the platform foundation."""

    template_name = "home.html"


class AboutView(TemplateView):
    """About page describing the project."""

    template_name = "about.html"
