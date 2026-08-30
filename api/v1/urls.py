"""API version 1 URL routing.

Populated incrementally with the approved endpoint structure. Currently
implements the authentication endpoints (register, login, refresh, logout,
``me``) and the role-based access endpoints that enforce the TENANT, LANDLORD
and ADMIN permission classes.
"""
from django.urls import path

from apps.accounts.views import (
    LandlordAreaView,
    LoginView,
    LogoutView,
    MeView,
    RefreshView,
    RegisterView,
    TenantAreaView,
    UserDetailView,
    UserListView,
)
from apps.apartments.views import (
    ApartmentDetailView,
    ApartmentListCreateView,
)
from apps.recommendations.views import (
    PreferenceDetailView,
    PreferenceListCreateView,
)
from apps.verification.views import (
    AdminVerificationApproveView,
    AdminVerificationListView,
    AdminVerificationRejectView,
    VerificationStatusView,
    VerificationSubmitView,
)

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("accounts/tenant/", TenantAreaView.as_view(), name="accounts-tenant"),
    path(
        "accounts/landlord/",
        LandlordAreaView.as_view(),
        name="accounts-landlord",
    ),
    path("accounts/users/", UserListView.as_view(), name="accounts-users"),
    path(
        "accounts/users/<int:pk>/",
        UserDetailView.as_view(),
        name="accounts-user-detail",
    ),
    path(
        "verification/submit/",
        VerificationSubmitView.as_view(),
        name="verification-submit",
    ),
    path(
        "verification/status/",
        VerificationStatusView.as_view(),
        name="verification-status",
    ),
    path(
        "admin/verifications/",
        AdminVerificationListView.as_view(),
        name="admin-verifications",
    ),
    path(
        "admin/verifications/<int:pk>/approve/",
        AdminVerificationApproveView.as_view(),
        name="admin-verification-approve",
    ),
    path(
        "admin/verifications/<int:pk>/reject/",
        AdminVerificationRejectView.as_view(),
        name="admin-verification-reject",
    ),
    path(
        "apartments/",
        ApartmentListCreateView.as_view(),
        name="apartment-create",
    ),
    path(
        "apartments/<int:pk>/",
        ApartmentDetailView.as_view(),
        name="apartment-detail",
    ),
    path(
        "preferences/",
        PreferenceListCreateView.as_view(),
        name="preference-list",
    ),
    path(
        "preferences/<int:pk>/",
        PreferenceDetailView.as_view(),
        name="preference-detail",
    ),
]
