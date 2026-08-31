"""
API tests for Phase 4, Sprint 4.4 - Tenant Preference Management.

These verify the Preference API (§24.3): list, create, retrieve, update and
delete of tenant preferences, including ownership restrictions (a tenant may
only manage their own preferences; an administrator may manage any; a landlord
may manage none) and value validation.
"""
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.apartments.models import Apartment
from apps.recommendations.models import Preference

User = get_user_model()

LOGIN_URL = "/api/v1/auth/login/"
PREFERENCE_LIST_URL = "/api/v1/preferences/"

PASSWORD = "StrongPass123!"


class PreferenceApiTests(APITestCase):
    def setUp(self):
        self.client = APIClient(HTTP_HOST="localhost")
        self.tenant = User.objects.create_user(
            email="tenant@example.com",
            password=PASSWORD,
            full_name="Tenant User",
            role=User.Role.TENANT,
        )
        self.other_tenant = User.objects.create_user(
            email="other@example.com",
            password=PASSWORD,
            full_name="Other Tenant",
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

    def _create_preference(self, tenant=None, **kwargs):
        defaults = {
            "location": "Calabar",
            "max_rent": "300000.00",
            "apartment_type": Apartment.ApartmentType.TWO_BEDROOM,
            "bedrooms": 2,
            "bathrooms": 2,
        }
        defaults.update(kwargs)
        return Preference.objects.create(tenant=tenant or self.tenant, **defaults)

    # --- Create ---

    def test_tenant_can_create_preference(self):
        self._auth_as(self.tenant)
        response = self.client.post(
            PREFERENCE_LIST_URL,
            {
                "location": "Calabar",
                "max_rent": "300000.00",
                "apartment_type": Apartment.ApartmentType.TWO_BEDROOM,
                "bedrooms": 2,
                "bathrooms": 2,
                "parking": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        data = response.data["data"]
        self.assertEqual(data["tenant"], self.tenant.pk)
        self.assertEqual(data["location"], "Calabar")
        self.assertTrue(data["parking"])
        self.assertEqual(Preference.objects.count(), 1)

    def test_create_assigns_owner_to_authenticated_tenant(self):
        self._auth_as(self.tenant)
        response = self.client.post(
            PREFERENCE_LIST_URL,
            {"location": "Uyo", "max_rent": "150000.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        preference = Preference.objects.get(pk=response.data["data"]["id"])
        self.assertEqual(preference.tenant, self.tenant)

    def test_create_rejects_negative_max_rent(self):
        self._auth_as(self.tenant)
        response = self.client.post(
            PREFERENCE_LIST_URL,
            {"location": "Calabar", "max_rent": "-1000.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("max_rent", response.data["errors"])

    def test_create_rejects_zero_bedrooms(self):
        self._auth_as(self.tenant)
        response = self.client.post(
            PREFERENCE_LIST_URL,
            {"location": "Calabar", "bedrooms": 0},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("bedrooms", response.data["errors"])

    def test_create_rejects_zero_bathrooms(self):
        self._auth_as(self.tenant)
        response = self.client.post(
            PREFERENCE_LIST_URL,
            {"location": "Calabar", "bathrooms": 0},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("bathrooms", response.data["errors"])

    def test_create_rejects_invalid_apartment_type(self):
        self._auth_as(self.tenant)
        response = self.client.post(
            PREFERENCE_LIST_URL,
            {"location": "Calabar", "apartment_type": "DETACHED_HOUSE"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("apartment_type", response.data["errors"])

    def test_landlord_cannot_create_preference(self):
        self._auth_as(self.landlord)
        response = self.client.post(
            PREFERENCE_LIST_URL,
            {"location": "Calabar", "max_rent": "200000.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_cannot_create_preference(self):
        self._auth_as(self.admin)
        response = self.client.post(
            PREFERENCE_LIST_URL,
            {"location": "Calabar", "max_rent": "200000.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_create_preference(self):
        response = self.client.post(
            PREFERENCE_LIST_URL,
            {"location": "Calabar", "max_rent": "200000.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- List ---

    def test_tenant_sees_only_own_preferences(self):
        self._create_preference(tenant=self.tenant, location="Calabar")
        self._create_preference(tenant=self.other_tenant, location="Uyo")
        self._auth_as(self.tenant)
        response = self.client.get(PREFERENCE_LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["tenant"], self.tenant.pk)

    def test_landlord_cannot_list_preferences(self):
        self._auth_as(self.landlord)
        response = self.client.get(PREFERENCE_LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_preference_list_is_paginated(self):
        self._create_preference(tenant=self.tenant, location="Calabar")
        self._create_preference(tenant=self.tenant, location="Uyo")
        self._auth_as(self.tenant)
        response = self.client.get(PREFERENCE_LIST_URL, {"page": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.data["page"], 1)
        self.assertEqual(response.data["pages"], 1)
        self.assertIsNone(response.data["next"])
        self.assertIsNone(response.data["previous"])
        self.assertEqual(len(response.data["data"]), 2)

    # --- Retrieve / Update / Delete ---

    def _detail_url(self, preference):
        return f"{PREFERENCE_LIST_URL}{preference.pk}/"

    def test_owner_can_retrieve_preference(self):
        preference = self._create_preference(tenant=self.tenant)
        self._auth_as(self.tenant)
        response = self.client.get(self._detail_url(preference))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["id"], preference.pk)

    def test_other_tenant_cannot_retrieve_preference(self):
        preference = self._create_preference(tenant=self.tenant)
        self._auth_as(self.other_tenant)
        response = self.client.get(self._detail_url(preference))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_landlord_cannot_retrieve_preference(self):
        preference = self._create_preference(tenant=self.tenant)
        self._auth_as(self.landlord)
        response = self.client.get(self._detail_url(preference))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_retrieve_any_preference(self):
        preference = self._create_preference(tenant=self.other_tenant)
        self._auth_as(self.admin)
        response = self.client.get(self._detail_url(preference))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["id"], preference.pk)

    def test_owner_can_update_preference(self):
        preference = self._create_preference(tenant=self.tenant, location="Calabar")
        self._auth_as(self.tenant)
        response = self.client.patch(
            self._detail_url(preference),
            {"location": "Uyo"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["location"], "Uyo")

    def test_update_rejects_invalid_value(self):
        preference = self._create_preference(tenant=self.tenant)
        self._auth_as(self.tenant)
        response = self.client.patch(
            self._detail_url(preference),
            {"max_rent": "-500.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("max_rent", response.data["errors"])

    def test_other_tenant_cannot_update_preference(self):
        preference = self._create_preference(tenant=self.tenant)
        self._auth_as(self.other_tenant)
        response = self.client.patch(
            self._detail_url(preference),
            {"location": "Uyo"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_update_preference(self):
        preference = self._create_preference(tenant=self.other_tenant)
        self._auth_as(self.admin)
        response = self.client.patch(
            self._detail_url(preference),
            {"location": "Abuja"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["location"], "Abuja")

    def test_owner_can_delete_preference(self):
        preference = self._create_preference(tenant=self.tenant)
        self._auth_as(self.tenant)
        response = self.client.delete(self._detail_url(preference))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Preference.objects.filter(pk=preference.pk).exists())

    def test_other_tenant_cannot_delete_preference(self):
        preference = self._create_preference(tenant=self.tenant)
        self._auth_as(self.other_tenant)
        response = self.client.delete(self._detail_url(preference))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Preference.objects.filter(pk=preference.pk).exists())

    def test_admin_can_delete_any_preference(self):
        preference = self._create_preference(tenant=self.other_tenant)
        self._auth_as(self.admin)
        response = self.client.delete(self._detail_url(preference))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Preference.objects.filter(pk=preference.pk).exists())

    def test_missing_preference_returns_404(self):
        self._auth_as(self.tenant)
        response = self.client.get(f"{PREFERENCE_LIST_URL}99999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
