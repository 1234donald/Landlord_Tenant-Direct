"""URL routing for the Administrator dashboard module (Phase 6, Sprint 6.1).

Admin-only presentation pages:
- ``/admin/dashboard/``             - system overview;
- ``/admin/dashboard/users/``       - user management overview;
- ``/admin/dashboard/landlords/``   - landlord management overview;
- ``/admin/dashboard/apartments/``  - apartment management overview;
- ``/admin/dashboard/verifications/`` - verification workflow overview.
"""
from django.urls import path

from .views import (
    ApartmentManagementView,
    DashboardView,
    LandlordManagementView,
    UserManagementView,
    VerificationOverviewView,
)

app_name = "admin_dashboard"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("users/", UserManagementView.as_view(), name="users"),
    path("landlords/", LandlordManagementView.as_view(), name="landlords"),
    path("apartments/", ApartmentManagementView.as_view(), name="apartments"),
    path("verifications/", VerificationOverviewView.as_view(), name="verifications"),
]
