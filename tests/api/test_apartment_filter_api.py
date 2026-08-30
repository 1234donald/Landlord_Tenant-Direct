"""
API tests for Phase 4, Sprint 4.2 - Combined Filtering and Pagination.

These verify the extended ``GET /api/v1/apartments/`` endpoint: facility and
availability filtering, pagination metadata, and rejection of invalid filter
values.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.apartments.models import Apartment

User = get_user_model()

APARTMENTS_URL = "/api/v1/apartments/"

PASSWORD = "StrongPass123!"


def make_landlord(email="landlord@example.com"):
    return User.objects.create_user(
        email=email,
        password=PASSWORD,
        full_name="Landlord User",
        role=User.Role.LANDLORD,
    )


def make_apartment(landlord, **kwargs):
    defaults = {
        "title": "Default Apartment",
        "description": "",
        "location": "Calabar",
        "address": "",
        "rental_price": Decimal("250000.00"),
        "apartment_type": "TWO_BEDROOM",
        "bedrooms": 2,
        "bathrooms": 2,
        "parking": False,
        "electricity": False,
        "water": False,
        "security": False,
        "furnished": False,
        "availability": True,
    }
    defaults.update(kwargs)
    return Apartment.objects.create(landlord=landlord, **defaults)


class ApartmentFilterApiTests(APITestCase):
    def setUp(self):
        self.client = APIClient(HTTP_HOST="localhost")
        self.landlord = make_landlord()

    def test_filter_by_parking_true(self):
        with_parking = make_apartment(self.landlord, title="With Parking", parking=True)
        make_apartment(self.landlord, title="No Parking")
        response = self.client.get(APARTMENTS_URL, {"parking": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data["data"]]
        self.assertIn(with_parking.pk, ids)
        self.assertEqual(len(ids), 1)

    def test_filter_by_multiple_facilities(self):
        both = make_apartment(
            self.landlord,
            title="Both",
            electricity=True,
            water=True,
        )
        make_apartment(self.landlord, title="Electricity Only", electricity=True)
        response = self.client.get(
            APARTMENTS_URL,
            {"electricity": "true", "water": "true"},
        )
        ids = [item["id"] for item in response.data["data"]]
        self.assertIn(both.pk, ids)
        self.assertEqual(len(ids), 1)

    def test_filter_by_furnished(self):
        furnished = make_apartment(self.landlord, title="Furnished", furnished=True)
        make_apartment(self.landlord, title="Unfurnished")
        response = self.client.get(APARTMENTS_URL, {"furnished": "1"})
        ids = [item["id"] for item in response.data["data"]]
        self.assertIn(furnished.pk, ids)
        self.assertEqual(len(ids), 1)

    def test_filter_by_availability_false(self):
        make_apartment(self.landlord, title="Available")
        unavailable = make_apartment(self.landlord, title="Unavailable", availability=False)
        response = self.client.get(APARTMENTS_URL, {"availability": "false"})
        ids = [item["id"] for item in response.data["data"]]
        self.assertIn(unavailable.pk, ids)
        self.assertEqual(len(ids), 1)

    def test_combined_filter_with_facilities_location_and_price(self):
        match = make_apartment(
            self.landlord,
            title="Match",
            location="Uyo",
            rental_price=Decimal("150000.00"),
            electricity=True,
            water=True,
        )
        make_apartment(
            self.landlord,
            title="Wrong Location",
            location="Calabar",
            rental_price=Decimal("150000.00"),
            electricity=True,
            water=True,
        )
        make_apartment(
            self.landlord,
            title="No Electricity",
            location="Uyo",
            rental_price=Decimal("150000.00"),
            water=True,
        )
        response = self.client.get(
            APARTMENTS_URL,
            {
                "location": "uyo",
                "max_price": "200000",
                "electricity": "true",
                "water": "true",
            },
        )
        ids = [item["id"] for item in response.data["data"]]
        self.assertIn(match.pk, ids)
        self.assertEqual(len(ids), 1)

    def test_invalid_facility_value_returns_400(self):
        response = self.client.get(APARTMENTS_URL, {"parking": "maybe"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("parking", response.data["errors"])

    def test_invalid_availability_value_returns_400(self):
        response = self.client.get(APARTMENTS_URL, {"availability": "sometimes"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("availability", response.data["errors"])


class ApartmentPaginationApiTests(APITestCase):
    def setUp(self):
        self.client = APIClient(HTTP_HOST="localhost")
        self.landlord = make_landlord()
        for index in range(25):
            make_apartment(
                self.landlord,
                title=f"Apartment {index}",
            )

    def test_pagination_metadata_is_present(self):
        response = self.client.get(APARTMENTS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 25)
        self.assertEqual(response.data["page"], 1)
        self.assertIsNotNone(response.data["next"])
        self.assertIsNone(response.data["previous"])
        # Page size is 12.
        self.assertEqual(len(response.data["data"]), 12)

    def test_pagination_page_two(self):
        response = self.client.get(APARTMENTS_URL, {"page": "2"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["page"], 2)
        self.assertEqual(len(response.data["data"]), 12)
        self.assertIsNotNone(response.data["next"])
        self.assertIsNotNone(response.data["previous"])

    def test_pagination_last_page(self):
        response = self.client.get(APARTMENTS_URL, {"page": "3"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["page"], 3)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertIsNone(response.data["next"])
        self.assertIsNotNone(response.data["previous"])

    def test_pagination_pages_beyond_last_return_empty(self):
        response = self.client.get(APARTMENTS_URL, {"page": "99"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["page"], 99)
        self.assertEqual(response.data["data"], [])
        self.assertIsNone(response.data["next"])

    def test_invalid_page_defaults_to_one(self):
        response = self.client.get(APARTMENTS_URL, {"page": "abc"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["page"], 1)
        self.assertEqual(len(response.data["data"]), 12)

    def test_pagination_preserves_filters(self):
        response = self.client.get(
            APARTMENTS_URL,
            {"page": "2", "location": "Calabar"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["page"], 2)
        self.assertEqual(response.data["count"], 25)
        self.assertIn("location=Calabar", response.data["next"])
