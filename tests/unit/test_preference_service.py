"""
Unit tests for Phase 4, Sprint 4.4 - Preference preparation service.

These verify that ``prepare_preference_data`` produces the stable,
recommendation-ready query payload for a stored tenant preference: correct
values, canonical decimal representation, raw apartment-type choice preserved,
and ``None`` preserved for unstated preferences (so the Phase 5 Weighted KNN
component can apply its own hard filters and encoding without an imposed
ordinal mapping).
"""
import django.test as django_tests
from django.contrib.auth import get_user_model

from apps.apartments.models import Apartment
from apps.recommendations.models import Preference
from apps.recommendations.services import (
    apartment_type_labels,
    prepare_preference_data,
)

User = get_user_model()

PASSWORD = "StrongPass123!"


def make_tenant(email="tenant@example.com"):
    return User.objects.create_user(
        email=email,
        password=PASSWORD,
        full_name="Tenant User",
        role=User.Role.TENANT,
    )


class PreferenceServiceTests(django_tests.TestCase):
    def setUp(self):
        self.tenant = make_tenant()

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

    def test_prepares_full_preference(self):
        preference = self._preference(
            parking=True,
            electricity=False,
            water=True,
            security=True,
            furnished=False,
            additional_facilities="Gym",
        )
        data = prepare_preference_data(preference)
        self.assertEqual(data["tenant_id"], self.tenant.pk)
        self.assertEqual(data["location"], "Calabar")
        self.assertEqual(data["max_rent"], "300000.00")
        self.assertEqual(data["apartment_type"], "TWO_BEDROOM")
        self.assertEqual(data["bedrooms"], 2)
        self.assertEqual(data["bathrooms"], 2)
        self.assertTrue(data["parking"])
        self.assertFalse(data["electricity"])
        self.assertTrue(data["water"])
        self.assertTrue(data["security"])
        self.assertFalse(data["furnished"])
        self.assertEqual(data["additional_facilities"], "Gym")

    def test_max_rent_is_canonical_string(self):
        data = prepare_preference_data(self._preference(max_rent="250000.50"))
        self.assertEqual(data["max_rent"], "250000.50")

    def test_unstated_preferences_preserved_as_none(self):
        data = prepare_preference_data(self._preference())
        self.assertIsNone(data["parking"])
        self.assertIsNone(data["electricity"])
        self.assertIsNone(data["water"])
        self.assertIsNone(data["security"])
        self.assertIsNone(data["furnished"])

    def test_blank_location_and_facilities_become_none(self):
        data = prepare_preference_data(self._preference(location="", additional_facilities=""))
        self.assertIsNone(data["location"])
        self.assertIsNone(data["additional_facilities"])

    def test_unset_type_kept_as_none(self):
        data = prepare_preference_data(self._preference(apartment_type=None))
        self.assertIsNone(data["apartment_type"])

    def test_returns_plain_dict_with_expected_keys(self):
        data = prepare_preference_data(self._preference())
        expected_keys = {
            "tenant_id",
            "location",
            "max_rent",
            "apartment_type",
            "bedrooms",
            "bathrooms",
            "parking",
            "electricity",
            "water",
            "security",
            "furnished",
            "additional_facilities",
        }
        self.assertEqual(set(data.keys()), expected_keys)

    def test_prepare_does_not_write_any_data(self):
        self._preference()
        count_before = Preference.objects.count()
        for preference in Preference.objects.all():
            prepare_preference_data(preference)
        self.assertEqual(Preference.objects.count(), count_before)

    def test_apartment_type_labels_match_apartment_model(self):
        self.assertEqual(
            set(apartment_type_labels()),
            set(Apartment.ApartmentType.choices),
        )
