"""
API tests for Phase 2, Sprint 2.5 - Permissions and Role-Based Access.

These verify the role permission classes (IsTenant, IsLandlord, IsAdmin,
IsOwnerOrAdmin) and the protected endpoints that enforce role-based access
control. Key exit criteria: tenants cannot access landlord/admin functions,
landlords cannot access admin functions, and administrator routes are
protected.
"""
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

User = get_user_model()

LOGIN_URL = "/api/v1/auth/login/"
TENANT_URL = "/api/v1/accounts/tenant/"
LANDLORD_URL = "/api/v1/accounts/landlord/"
USERS_URL = "/api/v1/users/"

PASSWORD = "StrongPass123!"


class PermissionApiTests(APITestCase):
    def setUp(self):
        self.client = APIClient(HTTP_HOST="localhost")
        self.tenant = User.objects.create_user(
            email="tenant@example.com",
            password=PASSWORD,
            full_name="Tenant User",
            role=User.Role.TENANT,
        )
        self.landlord = User.objects.create_user(
            email="landlord@example.com",
            password=PASSWORD,
            full_name="Landlord User",
            role=User.Role.LANDLORD,
        )
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password=PASSWORD,
            full_name="Admin User",
            role=User.Role.ADMIN,
        )

    def _auth_as(self, user):
        response = self.client.post(
            LOGIN_URL,
            {"email": user.email, "password": PASSWORD},
            format="json",
        )
        access = response.data["data"]["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def test_unauthenticated_access_is_rejected(self):
        response = self.client.get(TENANT_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_tenant_can_access_tenant_endpoint(self):
        self._auth_as(self.tenant)
        response = self.client.get(TENANT_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

    def test_landlord_cannot_access_tenant_endpoint(self):
        self._auth_as(self.landlord)
        response = self.client.get(TENANT_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_cannot_access_tenant_endpoint(self):
        self._auth_as(self.admin)
        response = self.client.get(TENANT_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_landlord_can_access_landlord_endpoint(self):
        self._auth_as(self.landlord)
        response = self.client.get(LANDLORD_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

    def test_tenant_cannot_access_landlord_endpoint(self):
        self._auth_as(self.tenant)
        response = self.client.get(LANDLORD_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_cannot_access_landlord_endpoint(self):
        self._auth_as(self.admin)
        response = self.client.get(LANDLORD_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_tenant_cannot_access_admin_user_list(self):
        self._auth_as(self.tenant)
        response = self.client.get(USERS_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_landlord_cannot_access_admin_user_list(self):
        self._auth_as(self.landlord)
        response = self.client.get(USERS_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_access_user_list(self):
        self._auth_as(self.admin)
        response = self.client.get(USERS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        emails = {u["email"] for u in response.data["data"]}
        self.assertIn("tenant@example.com", emails)
        self.assertIn("landlord@example.com", emails)

    def test_canonical_users_endpoint_is_api_v1_users(self):
        # The canonical users collection endpoint is /api/v1/users/ (AGENTS 21).
        self._auth_as(self.admin)
        response = self.client.get("/api/v1/users/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        emails = {u["email"] for u in response.data["data"]}
        self.assertIn("tenant@example.com", emails)

    def test_legacy_users_alias_remains_available(self):
        # Backward-compatible alias /api/v1/accounts/users/ still resolves.
        self._auth_as(self.admin)
        response = self.client.get("/api/v1/accounts/users/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        emails = {u["email"] for u in response.data["data"]}
        self.assertIn("tenant@example.com", emails)

    def test_owner_can_view_own_profile_via_detail(self):
        self._auth_as(self.tenant)
        response = self.client.get(f"{USERS_URL}{self.tenant.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["email"], "tenant@example.com")

    def test_user_cannot_view_another_users_profile(self):
        self._auth_as(self.tenant)
        response = self.client.get(f"{USERS_URL}{self.landlord.pk}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_view_any_user_profile(self):
        self._auth_as(self.admin)
        response = self.client.get(f"{USERS_URL}{self.landlord.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["email"], "landlord@example.com")
