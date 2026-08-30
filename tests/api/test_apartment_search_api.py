"""
API tests for Phase 4, Sprint 4.1 - Basic Apartment Search.

These verify the public ``GET /api/v1/apartments/`` search endpoint: searching
by location, apartment type, price (minimum/maximum), bedrooms and bathrooms,
combined criteria, and rejection of invalid search parameter values.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.apartments.models import Apartment

User = get_user_model()

LOGIN_URL = "/api/v1/auth/login/"
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
        "availability": True,
    }
    defaults.update(kwargs)
    return Apartment.objects.create(landlord=landlord, **defaults)


class ApartmentSearchApiTests(APITestCase):
    def setUp(self):
        self.client = APIClient(HTTP_HOST="localhost")
        self.landlord = make_landlord()
        self.apartment = make_apartment(
            self.landlord,
            title="Sunny Two-Bedroom",
            location="Calabar",
            rental_price=Decimal("250000.00"),
            apartment_type="TWO_BEDROOM",
            bedrooms=2,
            bathrooms=2,
        )

    def _ids(self, response):
        return [item["id"] for item in response.data["data"]]

    def test_search_is_public_without_authentication(self):
        response = self.client.get(APARTMENTS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn(self.apartment.pk, self._ids(response))

    def test_returns_all_when_no_criteria(self):
        make_apartment(self.landlord, title="Another Flat")
        response = self.client.get(APARTMENTS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 2)

    def test_search_by_location_icontains(self):
        make_apartment(self.landlord, location="Uyo")
        response = self.client.get(APARTMENTS_URL, {"location": "calabar"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self._ids(response), [self.apartment.pk])

    def test_search_by_apartment_type(self):
        other = make_apartment(
            self.landlord,
            title="Duplex",
            apartment_type="DUPLEX",
        )
        response = self.client.get(APARTMENTS_URL, {"apartment_type": "TWO_BEDROOM"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.apartment.pk, self._ids(response))
        self.assertNotIn(other.pk, self._ids(response))

    def test_search_by_max_price(self):
        expensive = make_apartment(
            self.landlord,
            title="Expensive",
            rental_price=Decimal("900000.00"),
        )
        response = self.client.get(APARTMENTS_URL, {"max_price": "300000"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.apartment.pk, self._ids(response))
        self.assertNotIn(expensive.pk, self._ids(response))

    def test_search_by_min_price(self):
        cheap = make_apartment(
            self.landlord,
            title="Cheap",
            rental_price=Decimal("100000.00"),
        )
        response = self.client.get(APARTMENTS_URL, {"min_price": "200000"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.apartment.pk, self._ids(response))
        self.assertNotIn(cheap.pk, self._ids(response))

    def test_search_by_bedrooms(self):
        make_apartment(
            self.landlord,
            title="Three Bed",
            bedrooms=3,
        )
        response = self.client.get(APARTMENTS_URL, {"bedrooms": "2"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self._ids(response), [self.apartment.pk])

    def test_search_by_bathrooms(self):
        make_apartment(
            self.landlord,
            title="Three Bath",
            bathrooms=3,
        )
        response = self.client.get(APARTMENTS_URL, {"bathrooms": "2"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self._ids(response), [self.apartment.pk])

    def test_search_combined_criteria(self):
        wrong_type = make_apartment(
            self.landlord,
            title="Wrong Type",
            location="Calabar",
            rental_price=Decimal("200000.00"),
            apartment_type="DUPLEX",
            bedrooms=2,
            bathrooms=2,
        )
        other_location = make_apartment(
            self.landlord,
            title="Wrong Location",
            location="Uyo",
            rental_price=Decimal("200000.00"),
            apartment_type="TWO_BEDROOM",
            bedrooms=2,
            bathrooms=2,
        )
        response = self.client.get(
            APARTMENTS_URL,
            {
                "location": "calabar",
                "apartment_type": "TWO_BEDROOM",
                "max_price": "300000",
                "bedrooms": "2",
                "bathrooms": "2",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = self._ids(response)
        # The setup apartment matches every criterion; the wrong-type and
        # wrong-location apartments must be filtered out.
        self.assertIn(self.apartment.pk, ids)
        self.assertNotIn(wrong_type.pk, ids)
        self.assertNotIn(other_location.pk, ids)

    def test_search_returns_empty_when_no_match(self):
        response = self.client.get(APARTMENTS_URL, {"location": "nonexistent"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"], [])

    def test_invalid_apartment_type_returns_400(self):
        response = self.client.get(APARTMENTS_URL, {"apartment_type": "CASTLE"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("apartment_type", response.data["errors"])

    def test_invalid_max_price_returns_400(self):
        response = self.client.get(APARTMENTS_URL, {"max_price": "abc"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("max_price", response.data["errors"])

    def test_negative_max_price_returns_400(self):
        response = self.client.get(APARTMENTS_URL, {"max_price": "-5"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("max_price", response.data["errors"])

    def test_invalid_bedrooms_returns_400(self):
        response = self.client.get(APARTMENTS_URL, {"bedrooms": "many"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("bedrooms", response.data["errors"])

    def test_negative_bedrooms_returns_400(self):
        response = self.client.get(APARTMENTS_URL, {"bedrooms": "-1"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("bedrooms", response.data["errors"])

    def test_response_includes_apartment_details(self):
        response = self.client.get(APARTMENTS_URL, {"location": "Calabar"})
        item = response.data["data"][0]
        self.assertEqual(item["title"], "Sunny Two-Bedroom")
        self.assertEqual(item["location"], "Calabar")
        self.assertEqual(item["bedrooms"], 2)
