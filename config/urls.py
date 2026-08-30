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

from apps.core.views import AboutView, HomeView, handler404, handler500
from apps.apartments.presentation import (
    ApartmentBrowseView,
    ApartmentDetailPageView,
    MyApartmentsView,
)
from apps.recommendations.presentation import RecommendationResultsPageView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Administrator dashboard lives OUTSIDE Django admin (/admin/ is owned by
    # the Django admin site) to avoid its catch-all routing redirecting to the
    # admin login and to keep a dedicated admin-only console (Sprint 6.1).
    path("console/", include("apps.admin_dashboard.urls")),
    path("api/", include("api.urls")),
    path("about/", AboutView.as_view(), name="about"),
    path("my/apartments/", MyApartmentsView.as_view(), name="my-apartments"),
    path(
        "recommendations/",
        RecommendationResultsPageView.as_view(),
        name="recommendation-results",
    ),
    path(
        "apartments/<int:pk>/",
        ApartmentDetailPageView.as_view(),
        name="apartment-detail",
    ),
    path("apartments/", ApartmentBrowseView.as_view(), name="apartment-list"),
    path("", HomeView.as_view(), name="home"),
]

# Serve user-uploaded media and static files during development only.
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# Custom error handlers (Sprint 6.3 "secure error responses"). Django's
# ROOT_URLCONF automatically uses the module-level ``handler404``/``handler500``
# imported above to render clean, non-leaking error pages.
