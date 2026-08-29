"""API version 1 URL routing.

Populated incrementally with the approved endpoint structure. Currently only
the authentication registration endpoint is implemented; the remaining auth
endpoints (login, refresh, logout, me) arrive in Sprint 2.3.
"""
from django.urls import path

from apps.accounts.views import RegisterView

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
]
