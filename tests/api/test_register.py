"""
API tests for Phase 2, Sprint 2.2 - Registration.

These verify the public registration endpoint ``POST /api/v1/auth/register/``:
successful tenant/landlord registration, email/password/role validation,
duplicate-account prevention, and the response envelope.
"""
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

User = get_user_model()

REGISTER_URL = "/api/v1/auth/register/"


class RegistrationApiTests(APITestCase):
    def setUp(self):
        # The test host must be in ALLOWED_HOSTS (the default ``testserver`` is
        # intentionally not allowed).
        self.client = APIClient(HTTP_HOST="localhost")

    def _payload(self, **overrides):
        data = {
            "email": "tenant@example.com",
            "full_name": "Tenant One",
            "phone": "08012345678",
            "password": "StrongPass123!",
            "role": User.Role.TENANT,
        }
        data.update(overrides)
        return data

    def test_tenant_registration_succeeds(self):
        response = self.client.post(REGISTER_URL, self._payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["message"], "Registration successful.")
        self.assertEqual(response.data["data"]["email"], "tenant@example.com")
        self.assertEqual(response.data["data"]["role"], User.Role.TENANT)
        self.assertNotIn("password", response.data["data"])

    def test_landlord_registration_succeeds(self):
        response = self.client.post(
            REGISTER_URL,
            self._payload(role=User.Role.LANDLORD),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="tenant@example.com")
        self.assertEqual(user.role, User.Role.LANDLORD)

    def test_password_is_hashed(self):
        self.client.post(REGISTER_URL, self._payload(), format="json")
        user = User.objects.get(email="tenant@example.com")
        self.assertTrue(user.password.startswith("pbkdf2_"))
        self.assertNotEqual(user.password, "StrongPass123!")

    def test_duplicate_email_is_rejected(self):
        self.client.post(REGISTER_URL, self._payload(), format="json")
        response = self.client.post(REGISTER_URL, self._payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("email", response.data["errors"])
        self.assertEqual(User.objects.filter(email="tenant@example.com").count(), 1)

    def test_invalid_email_format_is_rejected(self):
        response = self.client.post(
            REGISTER_URL,
            self._payload(email="not-an-email"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data["errors"])

    def test_admin_role_is_rejected(self):
        response = self.client.post(
            REGISTER_URL,
            self._payload(role=User.Role.ADMIN),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("role", response.data["errors"])

    def test_weak_password_is_rejected(self):
        response = self.client.post(
            REGISTER_URL,
            self._payload(password="123"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data["errors"])
        self.assertFalse(User.objects.filter(email="tenant@example.com").exists())

    def test_missing_required_fields_is_rejected(self):
        response = self.client.post(
            REGISTER_URL,
            {"email": "x@example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("full_name", response.data["errors"])
        self.assertIn("password", response.data["errors"])

    def test_email_is_lowercased_and_unique(self):
        self.client.post(REGISTER_URL, self._payload(email="Case@Example.COM"), format="json")
        user = User.objects.get(email="case@example.com")
        self.assertEqual(user.email, "case@example.com")
        response = self.client.post(
            REGISTER_URL,
            self._payload(email="CASE@example.com"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_method_on_register_returns_405(self):
        response = self.client.get(REGISTER_URL)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertFalse(response.data["success"])
