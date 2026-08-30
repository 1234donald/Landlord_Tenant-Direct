"""URL routing for the Administrator dashboard module (Phase 6, Sprints 6.1-6.2).

Admin-only presentation pages:
- ``/console/``                       - system overview (Sprint 6.1);
- ``/console/users/``                 - user management;
- ``/console/landlords/``             - landlord management;
- ``/console/apartments/``            - apartment management;
- ``/console/verifications/``         - verification overview.

Admin workflow actions (Sprint 6.2):
- ``/console/reports/``               - administrative reports;
- ``/console/users/<id>/status/``     - user status management (POST);
- ``/console/apartments/<id>/moderate/`` - apartment moderation (POST);
- ``/console/verifications/<id>/review/`` - verification approve/reject (POST).
"""
from django.urls import path

from .views import (
    ApartmentManagementView,
    ApartmentModerationView,
    DashboardView,
    LandlordManagementView,
    ReportsView,
    UserManagementView,
    UserStatusActionView,
    VerificationActionView,
    VerificationOverviewView,
)

app_name = "admin_dashboard"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("users/", UserManagementView.as_view(), name="users"),
    path("users/<int:pk>/status/", UserStatusActionView.as_view(), name="user-status"),
    path("landlords/", LandlordManagementView.as_view(), name="landlords"),
    path("apartments/", ApartmentManagementView.as_view(), name="apartments"),
    path(
        "apartments/<int:pk>/moderate/",
        ApartmentModerationView.as_view(),
        name="apartment-moderate",
    ),
    path("verifications/", VerificationOverviewView.as_view(), name="verifications"),
    path(
        "verifications/<int:pk>/review/",
        VerificationActionView.as_view(),
        name="verification-review",
    ),
    path("reports/", ReportsView.as_view(), name="reports"),
]
