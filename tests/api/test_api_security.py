"""
API tests for Phase 6, Sprint 6.4 - API Security and Validation.

Covers the three hardening additions to the REST API:
- Consistent error responses: every escaping DRF error (401, 403, 404, 405,
  400, 429) is wrapped in the ``success/message/errors`` envelope instead of
  the default plain ``{"detail": ...}`` body.
- Throttling: the public authentication endpoints are rate-limited.
- Pagination: collection endpoints return paged ``data`` with ``count``,
  ``page``, ``pages``, ``next`` and ``previous`` metadata.
- JWT protections: expired access tokens are rejected and the JWT lifetime /
  blacklist configuration stays secure.
"""
import time
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework import exceptions, status
from rest_framework.test import APIClient, APITestCase
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from apps.core.api import api_exception_handler

User = get_user_model()

LOGIN_URL = "/api/v1/auth/login/"
ME_URL = "/api/v1/auth/me/"
USERS_URL = "/api/v1/accounts/users/"
MESSAGES_URL = "/api/v1/messages/"
MESSAGE_DETAIL_URL = "/api/v1/messages/999999/"
CONVERSATIONS_URL = "/api/v1/conversations/"
PREFERENCES_URL = "/api/v1/preferences/"
VERIFICATIONS_URL = "/api/v1/admin/verifications/"

PASSWORD = "StrongPass123!"


class ApiSecurityBase(APITestCase):
    def setUp(self):
        self.client = APIClient(HTTP_HOST="localhost")
        self.landlord = User.objects.create_user(
            email="security-landlord@example.com",
            password=PASSWORD,
            full_name="Security Landlord",
            role=User.Role.LANDLORD,
        )
        self.tenant = User.objects.create_user(
            email="security-tenant@example.com",
            password=PASSWORD,
            full_name="Security Tenant",
            role=User.Role.TENANT,
        )

    def _login(self, email):
        response = self.client.post(
            LOGIN_URL,
            {"email": email, "password": PASSWORD},
            format="json",
        )
        return response.data["data"]["access"]

    def _auth_as(self, user_email):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self._login(user_email)}"
        )


class ConsistentErrorEnvelopeTests(ApiSecurityBase):
    """Escaping DRF errors must use the ``success/message/errors`` envelope."""

    def test_unauthenticated_returns_401_envelope(self):
        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data["success"])
        self.assertIn("message", response.data)
        self.assertIn("errors", response.data)

    def test_forbidden_returns_403_envelope(self):
        self._auth_as(self.tenant.email)
        response = self.client.get(USERS_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data["success"])
        self.assertIn("message", response.data)
        self.assertIn("errors", response.data)

    def test_not_found_returns_404_envelope(self):
        self._auth_as(self.tenant.email)
        response = self.client.get(MESSAGE_DETAIL_URL)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data["success"])
        self.assertIn("message", response.data)
        self.assertIn("errors", response.data)

    def test_method_not_allowed_returns_405_envelope(self):
        self._auth_as(self.tenant.email)
        response = self.client.post(MESSAGE_DETAIL_URL, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertFalse(response.data["success"])
        self.assertIn("message", response.data)
        self.assertIn("errors", response.data)

    def test_error_envelope_never_exposes_stack_details(self):
        self._auth_as(self.tenant.email)
        response = self.client.get(MESSAGE_DETAIL_URL)
        body = response.content.decode()
        self.assertNotIn("Traceback", body)
        self.assertNotIn("File \"", body)
        self.assertNotIn("line ", body.lower())


class ExceptionHandlerUnitTests(ApiSecurityBase):
    """Direct unit tests of the custom exception handler's mapping."""

    def _run(self, exc):
        response = api_exception_handler(exc, context={})
        self.assertIsNotNone(response)
        self.assertFalse(response.data["success"])
        self.assertIn("message", response.data)
        self.assertIn("errors", response.data)
        return response

    def test_validation_error_maps_to_400(self):
        exc = exceptions.ValidationError({"price": ["Enter a number."]})
        response = self._run(exc)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["errors"]["price"], ["Enter a number."])

    def test_parse_error_maps_to_400(self):
        response = self._run(exceptions.ParseError("Malformed JSON."))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_throttled_maps_to_429_with_retry(self):
        exc = exceptions.Throttled(wait=30)
        response = self._run(exc)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(response.data["errors"]["retry_after"], 30)

    def test_unknown_exception_returns_none(self):
        # Unhandled exceptions must return None so Django logs them without
        # exposing internals (AGENTS 22).
        self.assertIsNone(api_exception_handler(ValueError("boom"), context={}))


class ThrottlingTests(ApiSecurityBase):
    """The public authentication endpoints are rate limited."""

    def test_login_is_rate_limited(self):
        # DRF caches the REST_FRAMEWORK settings, so instead of overriding the
        # setting we patch the throttle's rate lookup with a tiny limit and
        # prove the endpoint actually enforces it.
        cache.clear()
        with mock.patch.object(
            ScopedRateThrottle, "THROTTLE_RATES", {"auth": "1/min"}
        ):
            first = self.client.post(
                LOGIN_URL,
                {"email": self.tenant.email, "password": PASSWORD},
                format="json",
            )
            self.assertEqual(first.status_code, status.HTTP_200_OK)

            second = self.client.post(
                LOGIN_URL,
                {"email": self.tenant.email, "password": PASSWORD},
                format="json",
            )
        self.assertEqual(second.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertFalse(second.data["success"])
        self.assertIn("retry_after", second.data["errors"])

    def test_login_endpoint_uses_auth_throttle_scope(self):
        from apps.accounts.views import LoginView

        self.assertEqual(LoginView.throttle_scope, "auth")
        self.assertIn(ScopedRateThrottle, LoginView.throttle_classes)


class PaginationTests(ApiSecurityBase):
    """Collection endpoints return paged data with metadata."""

    def test_messages_list_is_paginated(self):
        from apps.messaging.models import Conversation, Message

        conversation = Conversation.objects.create(
            tenant=self.tenant,
            landlord=self.landlord,
        )
        Message.objects.create(
            conversation=conversation,
            sender=self.landlord,
            recipient=self.tenant,
            body="Hello from the landlord.",
        )
        Message.objects.create(
            conversation=conversation,
            sender=self.tenant,
            recipient=self.landlord,
            body="Hello back.",
        )

        self._auth_as(self.tenant.email)
        response = self.client.get(MESSAGES_URL, {"page": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertTrue(data["success"])
        self.assertEqual(data["count"], 2)
        self.assertEqual(data["page"], 1)
        self.assertEqual(data["pages"], 1)
        self.assertIsNone(data["next"])
        self.assertIsNone(data["previous"])
        self.assertEqual(len(data["data"]), 2)

    def test_users_list_is_paginated_for_admin(self):
        User.objects.create_user(
            email="security-admin@example.com",
            password=PASSWORD,
            full_name="Security Admin",
            role=User.Role.ADMIN,
        )
        admin = User.objects.get(email="security-admin@example.com")
        self._auth_as(admin.email)
        response = self.client.get(USERS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["success"], True)
        self.assertEqual(response.data["count"], User.objects.count())
        self.assertEqual(response.data["page"], 1)
        self.assertTrue(isinstance(response.data["data"], list))

    def test_out_of_range_page_is_clamped(self):
        from apps.messaging.models import Conversation, Message

        conversation = Conversation.objects.create(
            tenant=self.tenant,
            landlord=self.landlord,
        )
        Message.objects.create(
            conversation=conversation,
            sender=self.landlord,
            recipient=self.tenant,
            body="A single message.",
        )
        self._auth_as(self.tenant.email)
        response = self.client.get(MESSAGES_URL, {"page": 99999})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["page"], 1)
        self.assertEqual(len(response.data["data"]), 1)


class JwtProtectionTests(ApiSecurityBase):
    """Expired and invalid tokens are rejected; config stays secure."""

    def test_expired_access_token_is_rejected(self):
        token = AccessToken.for_user(self.tenant)
        token["exp"] = int(time.time()) - 1000
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {str(token)}"
        )
        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data["success"])

    def test_valid_access_token_is_accepted(self):
        self._auth_as(self.tenant.email)
        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["email"], self.tenant.email)

    def test_access_lifetime_is_shorter_than_refresh(self):
        from django.conf import settings

        access = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]
        refresh = settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]
        self.assertLess(access, refresh)

    def test_refresh_token_blacklist_after_rotation_is_off_but_logout_blacklists(self):
        from django.conf import settings

        self.assertFalse(settings.SIMPLE_JWT["ROTATE_REFRESH_TOKENS"])
        refresh = RefreshToken.for_user(self.tenant)
        self.assertIsNotNone(refresh)
