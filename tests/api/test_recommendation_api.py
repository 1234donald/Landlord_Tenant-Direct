"""
API tests for Phase 5, Sprint 5.6 - Recommendation integration.

These verify the recommendation API (§24.4): generate, list and retrieve a
persisted recommendation run, the preference-to-recommendation flow, role
enforcement (TENANT only; landlord denied; unauthenticated denied), and error
handling when the tenant has no preference.
"""
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.apartments.models import Apartment
from apps.recommendations.models import Preference, Recommendation, RecommendationItem

User = get_user_model()

LOGIN_URL = "/api/v1/auth/login/"
GENERATE_URL = "/api/v1/recommendations/generate/"
LIST_URL = "/api/v1/recommendations/"

PASSWORD = "StrongPass123!"


class RecommendationApiTests(APITestCase):
    def setUp(self):
        self.client = APIClient(HTTP_HOST="localhost")
        self.tenant = User.objects.create_user(
            email="tenant@example.com",
            password=PASSWORD,
            full_name="Tenant",
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
            full_name="Landlord",
            role=User.Role.LANDLORD,
        )
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password=PASSWORD,
            full_name="Admin",
            role=User.Role.ADMIN,
        )
        self.apartment = Apartment.objects.create(
            landlord=self.landlord,
            title="Two-bedroom Flat",
            location="Calabar",
            rental_price="250000.00",
            apartment_type=Apartment.ApartmentType.TWO_BEDROOM,
            bedrooms=2,
            bathrooms=2,
        )

    def _auth_as(self, user):
        response = self.client.post(
            LOGIN_URL,
            {"email": user.email, "password": PASSWORD},
            format="json",
        )
        access = response.data["data"]["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def _preference(self, **kwargs):
        defaults = {
            "location": "Calabar",
            "max_rent": "300000.00",
            "apartment_type": Apartment.ApartmentType.TWO_BEDROOM,
            "bedrooms": 2,
            "bathrooms": 2,
        }
        defaults.update(kwargs)
        return Preference.objects.create(tenant=self.tenant, **defaults)

    # --- Generate ---

    def test_tenant_can_generate_recommendations(self):
        self._preference()
        self._auth_as(self.tenant)
        response = self.client.post(GENERATE_URL, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        data = response.data["data"]
        self.assertEqual(data["algorithm"], "weighted_knn")
        self.assertEqual(data["k"], 5)
        self.assertEqual(len(data["items"]), 1)
        item = data["items"][0]
        self.assertEqual(item["rank"], 1)
        self.assertEqual(item["apartment"]["id"], self.apartment.pk)

    def test_generate_persists_records(self):
        self._preference()
        self._auth_as(self.tenant)
        self.client.post(GENERATE_URL, {}, format="json")
        self.assertEqual(Recommendation.objects.count(), 1)
        self.assertEqual(RecommendationItem.objects.count(), 1)

    def test_generate_uses_latest_preference_by_default(self):
        self._preference()
        self._preference(location="Uyo")  # latest; should recommend nothing in Calabar... Uyo is eligible if apartment in Calabar? location filter excludes Calabar
        self._auth_as(self.tenant)
        response = self.client.post(GENERATE_URL, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # The apartment is in Calabar (not Uyo) -> hard filter excludes it.
        self.assertEqual(len(response.data["data"]["items"]), 0)

    def test_generate_with_explicit_preference_id(self):
        preference = self._preference()
        self._auth_as(self.tenant)
        response = self.client.post(
            GENERATE_URL, {"preference_id": preference.pk}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data["data"]["items"]), 1)

    def test_generate_without_preference_returns_400(self):
        self._auth_as(self.tenant)
        response = self.client.post(GENERATE_URL, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    def test_generate_with_foreign_preference_returns_400(self):
        foreign = Preference.objects.create(tenant=self.other_tenant, location="Uyo")
        self._auth_as(self.tenant)
        response = self.client.post(
            GENERATE_URL, {"preference_id": foreign.pk}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_generate_with_missing_preference_id_returns_404(self):
        self._auth_as(self.tenant)
        response = self.client.post(
            GENERATE_URL, {"preference_id": 9999}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_landlord_cannot_generate(self):
        self._auth_as(self.landlord)
        response = self.client.post(GENERATE_URL, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_generate(self):
        response = self.client.post(GENERATE_URL, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- List ---

    def test_tenant_lists_only_their_runs(self):
        self._preference()
        self._auth_as(self.tenant)
        self.client.post(GENERATE_URL, {}, format="json")

        self._auth_as(self.other_tenant)
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 0)

    def test_landlord_cannot_list(self):
        self._auth_as(self.landlord)
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_recommendation_list_is_paginated(self):
        self._preference()
        self._auth_as(self.tenant)
        self.client.post(GENERATE_URL, {}, format="json")
        response = self.client.get(LIST_URL, {"page": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["page"], 1)
        self.assertEqual(response.data["pages"], 1)
        self.assertIsNone(response.data["next"])
        self.assertIsNone(response.data["previous"])
        self.assertEqual(len(response.data["data"]), 1)

    # --- Detail ---

    def test_owner_can_retrieve_detail(self):
        preference = self._preference()
        self._auth_as(self.tenant)
        self.client.post(GENERATE_URL, {"preference_id": preference.pk}, format="json")
        run = Recommendation.objects.get()
        response = self.client.get(f"/api/v1/recommendations/{run.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]["items"]), 1)

    def test_other_tenant_cannot_retrieve_detail(self):
        preference = self._preference()
        self._auth_as(self.tenant)
        self.client.post(GENERATE_URL, {"preference_id": preference.pk}, format="json")
        run = Recommendation.objects.get()

        self._auth_as(self.other_tenant)
        response = self.client.get(f"/api/v1/recommendations/{run.pk}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_retrieve_detail(self):
        preference = self._preference()
        self._auth_as(self.tenant)
        self.client.post(GENERATE_URL, {"preference_id": preference.pk}, format="json")
        run = Recommendation.objects.get()

        self._auth_as(self.admin)
        response = self.client.get(f"/api/v1/recommendations/{run.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_detail_404_for_unknown_run(self):
        self._auth_as(self.tenant)
        response = self.client.get("/api/v1/recommendations/9999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)