"""
URL configuration for the Landlord-Tenant Direct Connect Platform.

Root routing includes:
- the Django admin interface;
- the versioned REST API at ``/api/`` (populated in later phases);
- the foundation home page.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.core.views import AboutView, HomeView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("about/", AboutView.as_view(), name="about"),
    path("", HomeView.as_view(), name="home"),
]

# Serve user-uploaded media and static files during development only.
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
