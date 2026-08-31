"""
API tests for Phase 2, Sprint 2.4 - Profile Management.

These verify that an authenticated user can view (``GET``) and edit (``PATCH``)
their own profile, that contact information can be changed, and that protected
identity fields (email, role) cannot be altered by the user.
"""
from django.contrib.auth import get_user_model
from rest_framework import status

from tests.api.base import BaseApiTestCase, LOGIN_URL, ME_URL, PASSWORD

User = get_user_model()


class ProfileApiTests(BaseApiTestCase):
    def setUp(self):
        super().setUp()
        self.user = self.make_landlord(
            email="profile@example.com",
            full_name="Original Name",
            phone="08000000000",
        )

    def _authenticate(self):
        self.auth_as(self.user)

    def _patch(self, payload):
        return self.client.patch(ME_URL, payload, format="json")

    def test_get_profile_requires_authentication(self):
        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_returns_own_profile(self):
        self._authenticate()
        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        self.assertEqual(data["email"], "profile@example.com")
        self.assertEqual(data["full_name"], "Original Name")
        self.assertEqual(data["role"], "LANDLORD")

    def test_patch_updates_full_name_and_phone(self):
        self._authenticate()
        response = self._patch(
            {"full_name": "Updated Name", "phone": "08111111111"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        data = response.data["data"]
        self.assertEqual(data["full_name"], "Updated Name")
        self.assertEqual(data["phone"], "08111111111")
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, "Updated Name")
        self.assertEqual(self.user.phone, "08111111111")

    def test_patch_updates_partial_fields(self):
        self._authenticate()
        response = self._patch({"phone": "08222222222"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone, "08222222222")
        # Unchanged fields are preserved.
        self.assertEqual(self.user.full_name, "Original Name")

    def test_email_and_role_are_read_only(self):
        self._authenticate()
        response = self._patch(
            {"email": "hacked@example.com", "role": "ADMIN"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "profile@example.com")
        self.assertEqual(self.user.role, "LANDLORD")

    def test_patch_rejects_blank_full_name(self):
        self._authenticate()
        response = self._patch({"full_name": ""})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    def test_tenant_can_manage_own_profile(self):
        tenant = User.objects.create_user(
            email="tenant@example.com",
            password=PASSWORD,
            full_name="Tenant User",
            role=User.Role.TENANT,
        )
        login = self.client.post(
            LOGIN_URL,
            {"email": "tenant@example.com", "password": PASSWORD},
            format="json",
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login.data['data']['access']}"
        )
        response = self._patch({"full_name": "Tenant Updated"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tenant.refresh_from_db()
        self.assertEqual(tenant.full_name, "Tenant Updated")
