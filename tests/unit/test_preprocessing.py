"""
Unit tests for Phase 5, Sprint 5.2 - Feature extraction and encoding.

These verify the feature-processing pipeline deliverable in ``ml.preprocessing``:
apartment- and tenant-vector construction, categorical (one-hot) encoding,
binary 0/1 encoding and missing-value handling. Numerical values are asserted as
raw (min-max normalisation is Sprint 5.3); no distance/ranking is computed here.
"""
import django.test as django_tests
from django.contrib.auth import get_user_model

from apps.apartments.models import Apartment
from apps.recommendations.models import Preference
from ml.features import BINARY_FEATURES, FEATURE_NAMES
from ml.preprocessing import (
    apartment_feature_vector,
    encode_apartment_vector,
    encode_binary,
    encode_tenant_vector,
    one_hot_columns,
    one_hot_encode_apartment_type,
    preference_feature_vector,
    validate_encoded_pair,
)

User = get_user_model()
PASSWORD = "StrongPass123!"


def make_landlord():
    return User.objects.create_user(
        email="landlord@example.com",
        password=PASSWORD,
        full_name="Landlord User",
        role=User.Role.LANDLORD,
    )


def make_tenant():
    return User.objects.create_user(
        email="tenant@example.com",
        password=PASSWORD,
        full_name="Tenant User",
        role=User.Role.TENANT,
    )


def make_apartment(landlord, **overrides):
    defaults = {
        "title": "Two-Bedroom Flat",
        "location": "Calabar",
        "rental_price": "250000.00",
        "apartment_type": Apartment.ApartmentType.TWO_BEDROOM,
        "bedrooms": 2,
        "bathrooms": 2,
        "parking": True,
        "electricity": True,
        "water": False,
        "security": True,
        "furnished": False,
    }
    defaults.update(overrides)
    return Apartment.objects.create(landlord=landlord, **defaults)


class EncodingHelperTests(django_tests.TestCase):
    def test_one_hot_columns_match_apartment_types(self):
        from ml.features import APARTMENT_TYPES

        self.assertEqual(
            set(one_hot_columns()),
            {f"apartment_type_{label}" for label in APARTMENT_TYPES},
        )

    def test_encode_binary(self):
        self.assertEqual(encode_binary(True), 1)
        self.assertEqual(encode_binary(False), 0)
        self.assertIsNone(encode_binary(None))

    def test_one_hot_encode_stated_type(self):
        encoded = one_hot_encode_apartment_type(Apartment.ApartmentType.TWO_BEDROOM)
        self.assertEqual(encoded["apartment_type_TWO_BEDROOM"], 1)
        self.assertEqual(encoded["apartment_type_ONE_BEDROOM"], 0)
        self.assertEqual(sum(encoded.values()), 1)

    def test_one_hot_encode_missing_type(self):
        encoded = one_hot_encode_apartment_type(None)
        self.assertEqual(sum(encoded.values()), 0)


class ApartmentVectorTests(django_tests.TestCase):
    def setUp(self):
        self.landlord = make_landlord()

    def test_apartment_feature_vector_covers_all_features(self):
        vector = apartment_feature_vector(make_apartment(self.landlord))
        self.assertEqual(set(vector), set(FEATURE_NAMES))
        self.assertEqual(vector["apartment_type"], Apartment.ApartmentType.TWO_BEDROOM)
        self.assertTrue(vector["parking"])
        self.assertFalse(vector["water"])

    def test_encode_apartment_vector_is_fully_encoded(self):
        apartment = make_apartment(self.landlord)
        vector = encode_apartment_vector(apartment)
        # Numerical raw, one-hot expanded, binaries 0/1.
        self.assertEqual(vector["rental_price"], 250000.0)
        self.assertEqual(vector["bedrooms"], 2.0)
        self.assertEqual(vector["apartment_type_TWO_BEDROOM"], 1)
        self.assertEqual(vector["apartment_type_DUPLEX"], 0)
        self.assertEqual(vector["parking"], 1)
        self.assertEqual(vector["water"], 0)
        self.assertEqual(vector["furnished"], 0)

    def test_encode_apartment_vector_has_no_missing_values(self):
        vector = encode_apartment_vector(make_apartment(self.landlord))
        self.assertNotIn(None, vector.values())


class TenantVectorTests(django_tests.TestCase):
    def setUp(self):
        self.tenant = make_tenant()

    def _preference(self, **kwargs):
        return Preference.objects.create(tenant=self.tenant, **kwargs)

    def test_preference_feature_vector_marks_missing_as_none(self):
        vector = preference_feature_vector(
            self._preference(location="Calabar", max_rent="300000.00")
        )
        self.assertEqual(set(vector), set(FEATURE_NAMES))
        self.assertEqual(vector["rental_price"], 300000.0)  # maps from max_rent
        self.assertIsNone(vector["parking"])

    def test_encode_tenant_vector_with_full_preferences(self):
        preference = self._preference(
            location="Calabar",
            max_rent="300000.00",
            apartment_type=Apartment.ApartmentType.TWO_BEDROOM,
            bedrooms=2,
            bathrooms=2,
            parking=True,
            electricity=False,
            water=True,
            security=True,
            furnished=False,
        )
        vector, mask = encode_tenant_vector(preference)
        self.assertEqual(vector["rental_price"], 300000.0)
        self.assertEqual(vector["apartment_type_TWO_BEDROOM"], 1)
        self.assertEqual(vector["parking"], 1)
        self.assertEqual(vector["electricity"], 0)
        self.assertTrue(mask["rental_price"])
        self.assertTrue(mask["parking"])
        self.assertTrue(mask["apartment_type_TWO_BEDROOM"])
        self.assertFalse(mask["apartment_type_DUPLEX"])

    def test_encode_tenant_vector_missing_facility_is_inactive(self):
        preference = self._preference(location="Calabar", water=True)
        vector, mask = encode_tenant_vector(preference)
        # Unstated facilities are None and inactive; stated water is active.
        self.assertIsNone(vector["parking"])
        self.assertFalse(mask["parking"])
        self.assertTrue(mask["water"])
        self.assertIsNone(vector["rental_price"])
        self.assertFalse(mask["rental_price"])

    def test_encode_tenant_vector_missing_type_has_no_active_column(self):
        preference = self._preference(location="Calabar")
        vector, mask = encode_tenant_vector(preference)
        self.assertEqual(sum(vector[col] for col in one_hot_columns()), 0)
        self.assertFalse(any(mask[col] for col in one_hot_columns()))


class VectorConsistencyTests(django_tests.TestCase):
    def setUp(self):
        self.landlord = make_landlord()
        self.tenant = make_tenant()

    def test_apartment_and_tenant_vectors_are_consistent_shape(self):
        apartment_vector = encode_apartment_vector(make_apartment(self.landlord))
        preference = Preference.objects.create(
            tenant=self.tenant,
            max_rent="300000.00",
            apartment_type=Apartment.ApartmentType.TWO_BEDROOM,
        )
        tenant_vector, active_mask = encode_tenant_vector(preference)
        self.assertTrue(validate_encoded_pair(apartment_vector, tenant_vector, active_mask))
        # Every encoded name lines up between the two sides.
        self.assertEqual(
            set(apartment_vector) - set(tenant_vector),
            set(),
        )

    def test_validate_rejects_mismatched_vectors(self):
        good = encode_apartment_vector(make_apartment(self.landlord))
        missing_key = dict(good)
        missing_key.pop("parking")
        dummy_mask = {k: True for k in good}
        self.assertFalse(validate_encoded_pair(good, missing_key, dummy_mask))
        self.assertFalse(validate_encoded_pair(good, good, {"x": True}))
