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
from apps.accounts.presentation import (
    LandlordDashboardView,
    LoginView,
    LogoutView,
    ProfileView,
    RegisterView,
    TenantDashboardView,
)
from apps.apartments.presentation import (
    ApartmentBrowseView,
    ApartmentCreateView,
    ApartmentDetailPageView,
    ApartmentEditView,
    MyApartmentsView,
)
from apps.messaging.presentation import (
    ConversationDetailView,
    ConversationListView,
    NewConversationView,
)
from apps.recommendations.presentation import (
    PreferenceFormPageView,
    RecommendationResultsPageView,
)
from apps.verification.presentation import LandlordVerificationView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Administrator dashboard lives OUTSIDE Django admin (/admin/ is owned by
    # the Django admin site) to avoid its catch-all routing redirecting to the
    # admin login and to keep a dedicated admin-only console (Sprint 6.1).
    path("console/", include("apps.admin_dashboard.urls")),
    path("api/", include("api.urls")),
    # Session-based authentication pages (frontend counterpart to the JWT API).
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", RegisterView.as_view(), name="register"),
    # Profile and role dashboards
    path("profile/", ProfileView.as_view(), name="profile-edit"),
    path(
        "tenant/",
        TenantDashboardView.as_view(),
        name="tenant-dashboard",
    ),
    path(
        "tenant/profile/",
        ProfileView.as_view(),
        name="tenant-profile",
    ),
    path(
        "tenant/preferences/",
        PreferenceFormPageView.as_view(),
        name="edit-preference",
    ),
    path(
        "tenant/messages/",
        ConversationListView.as_view(),
        name="tenant-messages",
    ),
    path(
        "conversations/new/",
        NewConversationView.as_view(),
        name="new-conversation",
    ),
    path(
        "conversations/<int:pk>/",
        ConversationDetailView.as_view(),
        name="conversation-detail",
    ),
    path(
        "landlord/",
        LandlordDashboardView.as_view(),
        name="landlord-dashboard",
    ),
    path(
        "landlord/profile/",
        ProfileView.as_view(),
        name="landlord-profile",
    ),
    path(
        "landlord/verification/",
        LandlordVerificationView.as_view(),
        name="verification-form",
    ),
    path(
        "landlord/messages/",
        ConversationListView.as_view(),
        name="landlord-messages",
    ),
    path(
        "landlord/apartments/create/",
        ApartmentCreateView.as_view(),
        name="apartment-create",
    ),
    path(
        "landlord/apartments/<int:pk>/edit/",
        ApartmentEditView.as_view(),
        name="apartment-edit",
    ),
    path("about/", AboutView.as_view(), name="about"),
    path("my/apartments/", MyApartmentsView.as_view(), name="my-apartments"),
    path(
        "recommendations/",
        RecommendationResultsPageView.as_view(),
        name="recommendation-results",
    ),
    path(
        "recommendations/recent/",
        RecommendationResultsPageView.as_view(),
        name="recent-recommendations",
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
