"""
Unit tests for Phase 4, Sprint 4.3 - Tenant Preference Data Model.

These verify the ``Preference`` model: the tenant relationship, preferred
location/price/type/size, facility preferences (including the "no preference"
state), validation rules and database indexes. They require a test database.
"""
import django.test as django_tests
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.apartments.models import Apartment
from apps.recommendations.models import Preference

User = get_user_model()

PASSWORD = "StrongPass123!"


def make_tenant(email="tenant@example.com"):
    return User.objects.create_user(
        email=email,
        password=PASSWORD,
        full_name="Tenant User",
        role=User.Role.TENANT,
    )


def make_preference(tenant=None, **kwargs):
    defaults = {
        "location": "Calabar",
        "max_rent": "300000.00",
        "apartment_type": Apartment.ApartmentType.TWO_BEDROOM,
        "bedrooms": 2,
        "bathrooms": 2,
    }
    defaults.update(kwargs)
    return Preference.objects.create(tenant=tenant or make_tenant(), **defaults)


class PreferenceModelTests(django_tests.TestCase):
    def test_tenant_relationship(self):
        tenant = make_tenant()
        preference = make_preference(tenant=tenant)
        self.assertEqual(preference.tenant, tenant)
        self.assertIn(preference, tenant.preferences.all())

    def test_preference_requires_a_tenant(self):
        with self.assertRaises(Exception):
            Preference.objects.create(
                location="Calabar",
                max_rent="300000.00",
                bedrooms=2,
                bathrooms=2,
            )

    def test_preference_attributes_are_stored(self):
        preference = make_preference(
            location="Uyo",
            max_rent="150000.00",
            apartment_type=Apartment.ApartmentType.SELF_CONTAINED,
            bedrooms=1,
            bathrooms=1,
        )
        self.assertEqual(preference.location, "Uyo")
        self.assertEqual(str(preference.max_rent), "150000.00")
        self.assertEqual(preference.apartment_type, "SELF_CONTAINED")
        self.assertEqual(preference.bedrooms, 1)
        self.assertEqual(preference.bathrooms, 1)

    def test_apartment_type_choices_match_apartment(self):
        self.assertEqual(
            set(Preference._meta.get_field("apartment_type").choices),
            set(Apartment.ApartmentType.choices),
        )

    def test_facility_preferences_are_nullable_by_default(self):
        preference = make_preference()
        self.assertIsNone(preference.parking)
        self.assertIsNone(preference.electricity)
        self.assertIsNone(preference.water)
        self.assertIsNone(preference.security)
        self.assertIsNone(preference.furnished)
        self.assertEqual(preference.additional_facilities, "")

    def test_facility_preferences_can_be_set(self):
        preference = make_preference(
            parking=True,
            electricity=False,
            water=True,
            security=True,
            furnished=False,
            additional_facilities="Swimming pool, gym",
        )
        self.assertTrue(preference.parking)
        self.assertFalse(preference.electricity)
        self.assertTrue(preference.water)
        self.assertTrue(preference.security)
        self.assertFalse(preference.furnished)
        self.assertEqual(preference.additional_facilities, "Swimming pool, gym")

    def test_optional_fields_default_to_blank_or_null(self):
        preference = make_preference(
            location="",
            max_rent=None,
            apartment_type=None,
            bedrooms=None,
            bathrooms=None,
        )
        self.assertEqual(preference.location, "")
        self.assertIsNone(preference.max_rent)
        self.assertIsNone(preference.apartment_type)
        self.assertIsNone(preference.bedrooms)
        self.assertIsNone(preference.bathrooms)

    def test_timestamps_are_populated(self):
        preference = make_preference()
        self.assertIsNotNone(preference.created_at)
        self.assertIsNotNone(preference.updated_at)

    def test_max_rent_must_be_positive(self):
        preference = make_preference(max_rent="-5000.00")
        with self.assertRaises(ValidationError):
            preference.full_clean()

    def test_bedroom_count_must_be_at_least_one(self):
        preference = make_preference(bedrooms=0)
        with self.assertRaises(ValidationError):
            preference.full_clean()

    def test_bathroom_count_must_be_at_least_one(self):
        preference = make_preference(bathrooms=0)
        with self.assertRaises(ValidationError):
            preference.full_clean()

    def test_valid_preference_passes_validation(self):
        preference = make_preference()
        try:
            preference.full_clean()
        except ValidationError:
            self.fail("A valid preference must pass full_clean().")

    def test_string_representation_includes_tenant_and_id(self):
        preference = make_preference()
        self.assertIn("Preference", str(preference))
        self.assertIn(str(preference.id), str(preference))

    def test_default_ordering_newest_first(self):
        tenant = make_tenant()
        a = make_preference(tenant=tenant)
        b = make_preference(tenant=tenant)
        self.assertEqual(
            list(Preference.objects.all()),
            [b, a],
        )

    def test_required_query_fields_are_indexed(self):
        indexed_fields = {
            index.fields[0]
            for index in Preference._meta.indexes
        }
        for field in ("tenant", "location", "max_rent", "apartment_type"):
            self.assertIn(field, indexed_fields)
