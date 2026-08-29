"""
URL configuration for the Landlord-Tenant Direct Connect Platform.

Root routing includes:
- the Django admin interface;
- the versioned REST API at ``/api/`` (populated in later phases);
- the foundation home page.
"""
from django.contrib import admin
from django.urls import include, path

from apps.core.views import HomeView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("", HomeView.as_view(), name="home"),
]
