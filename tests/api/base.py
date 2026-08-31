"""Shared API test infrastructure (Sprint 7.2).

A reusable ``BaseApiTestCase`` so individual API test modules do not each
re-implement user factories and JWT authentication. New API tests should
subclass ``BaseApiTestCase`` and reuse ``make_user/make_tenant/make_landlord/
make_admin`` and ``auth_as`` instead of copying the same helpers. The shared
URL constants mirror the REST layout under ``/api/v1/``.
"""
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase

User = get_user_model()

PASSWORD = "StrongPass123!"

LOGIN_URL = "/api/v1/auth/login/"
REGISTER_URL = "/api/v1/auth/register/"
ME_URL = "/api/v1/auth/me/"

APARTMENTS_URL = "/api/v1/apartments/"
PREFERENCES_URL = "/api/v1/preferences/"
RECOMMENDATIONS_URL = "/api/v1/recommendations/"
MESSAGES_URL = "/api/v1/messages/"
CONVERSATIONS_URL = "/api/v1/conversations/"
VERIFICATION_SUBMIT_URL = "/api/v1/verification/submit/"
VERIFICATION_STATUS_URL = "/api/v1/verification/status/"
ADMIN_VERIFICATIONS_URL = "/api/v1/admin/verifications/"
USERS_URL = "/api/v1/accounts/users/"


class BaseApiTestCase(APITestCase):
    """Base for API tests: provides a host-aware client and role factories.

    The default ``APITestCase`` client uses ``testserver`` which is not in
    ``ALLOWED_HOSTS``, so every subclass-friendly client is bound to
    ``localhost``.
    """

    password = PASSWORD

    def setUp(self):
        self.client = APIClient(HTTP_HOST="localhost")

    def make_user(self, role, **overrides):
        defaults = {
            "email": f"{role.lower()}@example.com",
            "password": self.password,
            "full_name": f"{role.title()} User",
            "role": role,
        }
        defaults.update(overrides)
        return User.objects.create_user(**defaults)

    def make_tenant(self, **overrides):
        return self.make_user(User.Role.TENANT, **overrides)

    def make_landlord(self, **overrides):
        return self.make_user(User.Role.LANDLORD, **overrides)

    def make_admin(self, **overrides):
        return self.make_user(User.Role.ADMIN, **overrides)

    def auth_as(self, user):
        response = self.client.post(
            LOGIN_URL,
            {"email": user.email, "password": self.password},
            format="json",
        )
        access = response.data["data"]["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        return response
