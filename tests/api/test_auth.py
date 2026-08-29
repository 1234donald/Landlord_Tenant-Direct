"""
API tests for Phase 2, Sprint 2.3 - Authentication.

These verify the JWT authentication flow: login (access + refresh tokens),
token refresh, logout (refresh-token blacklisting), and protected-endpoint
access control.
"""
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

User = get_user_model()

LOGIN_URL = "/api/v1/auth/login/"
REFRESH_URL = "/api/v1/auth/refresh/"
LOGOUT_URL = "/api/v1/auth/logout/"
ME_URL = "/api/v1/auth/me/"

PASSWORD = "StrongPass123!"


class AuthApiTests(APITestCase):
    def setUp(self):
        self.client = APIClient(HTTP_HOST="localhost")
        self.user = User.objects.create_user(
            email="auth@example.com",
            password=PASSWORD,
            full_name="Auth User",
            role=User.Role.TENANT,
        )

    def _login(self):
        return self.client.post(
            LOGIN_URL,
            {"email": "auth@example.com", "password": PASSWORD},
            format="json",
        )

    def _access(self):
        return self._login().data["data"]["access"]

    def test_login_returns_access_and_refresh_tokens(self):
        response = self._login()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        data = response.data["data"]
        self.assertIn("access", data)
        self.assertIn("refresh", data)
        self.assertEqual(data["user"]["email"], "auth@example.com")

    def test_login_with_wrong_password_is_rejected(self):
        response = self.client.post(
            LOGIN_URL,
            {"email": "auth@example.com", "password": "WrongPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data["success"])

    def test_login_with_unknown_email_is_rejected(self):
        response = self.client.post(
            LOGIN_URL,
            {"email": "nobody@example.com", "password": PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_exchanges_valid_token(self):
        refresh = self._login().data["data"]["refresh"]
        response = self.client.post(
            REFRESH_URL,
            {"refresh": refresh},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data["data"])

    def test_refresh_rejects_invalid_token(self):
        response = self.client.post(
            REFRESH_URL,
            {"refresh": "not-a-valid-token"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data["success"])

    def test_me_requires_authentication(self):
        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_profile_with_valid_token(self):
        access = self._access()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["email"], "auth@example.com")

    def test_logout_blacklists_refresh_token(self):
        refresh = self._login().data["data"]["refresh"]
        logout = self.client.post(
            LOGOUT_URL,
            {"refresh": refresh},
            format="json",
        )
        self.assertEqual(logout.status_code, status.HTTP_200_OK)
        # The blacklisted refresh token must no longer be usable to refresh.
        response = self.client.post(
            REFRESH_URL,
            {"refresh": refresh},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_inactive_user_cannot_login(self):
        self.user.is_active = False
        self.user.save()
        response = self._login()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
