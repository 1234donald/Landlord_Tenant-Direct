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
]
