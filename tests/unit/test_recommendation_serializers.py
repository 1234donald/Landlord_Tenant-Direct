"""
Unit tests for Phase 7, Sprint 7.1 - Recommendation serializers.

These construct the DRF serializers directly and verify preference value
validation (apartment type, max rent, bedroom/bathroom counts), tenant ownership
injection on create, and the read representations (nested ranked items,
preference_id source) without the HTTP layer (SYSTEM_REQUIREMENTS 41, AGENTS 23).
"""
import django.test as django_tests
from django.contrib.auth import get_user_model

from apps.apartments.models import Apartment
from apps.recommendations.models import (
    Preference,
    Recommendation,
    RecommendationItem,
)
from apps.recommendations.serializers import (
    PreferenceCreateSerializer,
    PreferenceSerializer,
    PreferenceUpdateSerializer,
    RecommendationItemSerializer,
    RecommendationSerializer,
)

User = get_user_model()
PASSWORD = "StrongPass123!"


def make_user(email, role):
    return User.objects.create_user(
        email=email, password=PASSWORD, full_name=email, role=role
    )


class _FakeRequest:
    def __init__(self, user):
        self.user = user


class PreferenceCreateSerializerTests(django_tests.TestCase):
    def setUp(self):
        self.tenant = make_user("tenant@example.com", User.Role.TENANT)
        self.context = {"request": _FakeRequest(self.tenant)}

    def valid_payload(self, **overrides):
        payload = {
            "location": "Calabar",
            "max_rent": "300000",
            "apartment_type": Apartment.ApartmentType.TWO_BEDROOM,
            "bedrooms": 2,
            "bathrooms": 2,
            "parking": True,
        }
        payload.update(overrides)
        return payload

    def test_valid_preference_is_accepted(self):
        serializer = PreferenceCreateSerializer(
            data=self.valid_payload(), context=self.context
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_create_injects_tenant_from_authenticated_user(self):
        serializer = PreferenceCreateSerializer(
            data=self.valid_payload(), context=self.context
        )
        self.assertTrue(serializer.is_valid())
        preference = serializer.save()
        self.assertEqual(preference.tenant, self.tenant)

    def test_invalid_apartment_type_is_rejected(self):
        serializer = PreferenceCreateSerializer(
            data=self.valid_payload(apartment_type="GUESTHOUSE"),
            context=self.context,
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("apartment_type", serializer.errors)

    def test_negative_max_rent_is_rejected(self):
        serializer = PreferenceCreateSerializer(
            data=self.valid_payload(max_rent="-1"), context=self.context
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("max_rent", serializer.errors)

    def test_zero_bedrooms_is_rejected(self):
        serializer = PreferenceCreateSerializer(
            data=self.valid_payload(bedrooms=0), context=self.context
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("bedrooms", serializer.errors)

    def test_zero_bathrooms_is_rejected(self):
        serializer = PreferenceCreateSerializer(
            data=self.valid_payload(bathrooms=0), context=self.context
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("bathrooms", serializer.errors)

    def test_partial_update_keeps_unstated_fields(self):
        preference = Preference.objects.create(
            tenant=self.tenant, location="Calabar", max_rent="300000"
        )
        serializer = PreferenceUpdateSerializer(
            preference, data={"bedrooms": 3}, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        preference = serializer.save()
        preference.refresh_from_db()
        self.assertEqual(preference.bedrooms, 3)
        self.assertEqual(float(preference.max_rent), 300000.0)


class PreferenceReadSerializerTests(django_tests.TestCase):
    def setUp(self):
        self.tenant = make_user("tenant@example.com", User.Role.TENANT)
        self.preference = Preference.objects.create(
            tenant=self.tenant, location="Calabar", max_rent="300000"
        )

    def test_preference_read_serializer_is_read_only(self):
        serializer = PreferenceSerializer(self.preference)
        for field in serializer.fields.values():
            self.assertTrue(field.read_only)

    def test_preference_read_exposes_tenant_email(self):
        data = PreferenceSerializer(self.preference).data
        self.assertEqual(data["tenant_email"], self.tenant.email)
        self.assertEqual(data["tenant"], self.tenant.pk)
        self.assertEqual(float(data["max_rent"]), 300000.0)


class RecommendationReadSerializerTests(django_tests.TestCase):
    def setUp(self):
        self.tenant = make_user("tenant@example.com", User.Role.TENANT)
        self.landlord = make_user("landlord@example.com", User.Role.LANDLORD)
        self.preference = Preference.objects.create(
            tenant=self.tenant, location="Calabar"
        )
        self.recommendation = Recommendation.objects.create(
            tenant=self.tenant, preference=self.preference
        )
        self.apartment = Apartment.objects.create(
            landlord=self.landlord,
            title="Flat",
            location="Calabar",
            rental_price="200000.00",
            apartment_type=Apartment.ApartmentType.TWO_BEDROOM,
            bedrooms=2,
            bathrooms=2,
        )
        self.item = RecommendationItem.objects.create(
            recommendation=self.recommendation,
            apartment=self.apartment,
            rank=1,
            distance=0.25,
            similarity=0.78,
        )

    def test_item_serializer_nests_apartment(self):
        data = RecommendationItemSerializer(self.item).data
        self.assertEqual(data["rank"], 1)
        self.assertEqual(data["apartment"]["id"], self.apartment.pk)
        self.assertAlmostEqual(data["distance"], 0.25)

    def test_recommendation_serializer_exposes_items_and_preference(self):
        data = RecommendationSerializer(self.recommendation).data
        self.assertEqual(data["preference_id"], self.preference.pk)
        self.assertEqual(data["algorithm"], Recommendation.Algorithm.WEIGHTED_KNN)
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["apartment"]["title"], "Flat")
