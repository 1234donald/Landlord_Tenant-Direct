"""
Unit tests for Phase 5, Sprint 5.3 - Numerical normalisation.

These verify the tested-normalisation-service deliverable in ``ml.preprocessing``:
min-max normalisation of numerical features (x' = (x-min)/(max-min)), division-by-
zero protection, normalising eligible apartment data against their own range, and
normalising tenant numerical preferences. Cases with known expected values are
included and the tests are deterministic (no randomness).
"""
import math

import django.test as django_tests
from django.contrib.auth import get_user_model

from apps.apartments.models import Apartment
from ml.features import BINARY_FEATURES, NUMERICAL_FEATURES
from ml.preprocessing import (
    encode_apartment_vector,
    feature_bounds,
    min_max_normalise,
    one_hot_columns,
)
from ml.preprocessing import (
    normalise_apartments,
    normalise_features,
    normalise_tenant_vector,
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


def encoded_apartment(price, beds, baths, type_col="apartment_type_TWO_BEDROOM", **facilities):
    """Build an encoded apartment vector dict in the Sprint 5.2 format."""
    vector = {
        "rental_price": float(price),
        "bedrooms": float(beds),
        "bathrooms": float(baths),
    }
    for column in one_hot_columns():
        vector[column] = 1 if column == type_col else 0
    for name in BINARY_FEATURES:
        vector[name] = int(facilities.get(name, False))
    return vector


class MinMaxNormaliseTests(django_tests.TestCase):
    def test_known_midpoint(self):
        self.assertEqual(min_max_normalise(200000, 100000, 300000), 0.5)

    def test_extremes(self):
        self.assertEqual(min_max_normalise(100000, 100000, 300000), 0.0)
        self.assertEqual(min_max_normalise(300000, 100000, 300000), 1.0)

    def test_negative_and_mixed_bounds(self):
        self.assertEqual(min_max_normalise(0, -10, 10), 0.5)
        self.assertEqual(min_max_normalise(-5, -10, 10), 0.25)

    def test_division_by_zero_returns_zero(self):
        # Constant feature across candidates must not cause a division error.
        self.assertEqual(min_max_normalise(250000, 250000, 250000), 0.0)
        self.assertEqual(min_max_normalise(5, 5, 5), 0.0)

    def test_none_passes_through(self):
        self.assertIsNone(min_max_normalise(None, 100000, 300000))


class FeatureBoundsTests(django_tests.TestCase):
    def test_bounds_are_per_feature_min_and_max(self):
        vectors = [
            encoded_apartment(100000, 1, 1),
            encoded_apartment(200000, 2, 2),
            encoded_apartment(300000, 3, 3),
        ]
        bounds = feature_bounds(vectors)
        self.assertEqual(bounds["rental_price"], (100000.0, 300000.0))
        self.assertEqual(bounds["bedrooms"], (1.0, 3.0))
        self.assertEqual(bounds["bathrooms"], (1.0, 3.0))

    def test_bounds_ignore_none_values(self):
        vectors = [
            {"rental_price": 100000.0, "bedrooms": 1.0, "bathrooms": 1.0},
            {"rental_price": 200000.0, "bedrooms": 2.0, "bathrooms": None},
            {"rental_price": 300000.0, "bedrooms": 3.0, "bathrooms": 2.0},
        ]
        bounds = feature_bounds(vectors)
        self.assertEqual(bounds["bathrooms"], (1.0, 2.0))

    def test_bounds_default_when_empty(self):
        bounds = feature_bounds([])
        for name in NUMERICAL_FEATURES:
            self.assertEqual(bounds[name], (0.0, 0.0))


class NormaliseApartmentsTests(django_tests.TestCase):
    def test_first_and_last_map_to_0_and_1(self):
        vectors = [
            encoded_apartment(100000, 1, 1),
            encoded_apartment(200000, 2, 2),
            encoded_apartment(300000, 3, 3),
        ]
        bounds, normalised = normalise_apartments(vectors)
        self.assertEqual(normalised[0]["rental_price"], 0.0)
        self.assertEqual(normalised[0]["bedrooms"], 0.0)
        self.assertEqual(normalised[2]["rental_price"], 1.0)
        self.assertEqual(normalised[2]["bedrooms"], 1.0)
        # The middle apartment sits at the midpoint of each numerical feature.
        self.assertAlmostEqual(normalised[1]["rental_price"], 0.5)
        self.assertAlmostEqual(normalised[1]["bedrooms"], 0.5)

    def test_non_numerical_dimensions_are_unchanged(self):
        vectors = [
            encoded_apartment(100000, 1, 1, type_col="apartment_type_ONE_BEDROOM", parking=True),
            encoded_apartment(300000, 3, 3, type_col="apartment_type_THREE_BEDROOM"),
        ]
        bounds, normalised = normalise_apartments(vectors)
        first = normalised[0]
        self.assertEqual(first["apartment_type_ONE_BEDROOM"], 1)
        self.assertEqual(first["apartment_type_TWO_BEDROOM"], 0)
        self.assertEqual(first["parking"], 1)
        self.assertEqual(first["furnished"], 0)

    def test_constant_feature_does_not_divide_by_zero(self):
        # All three have the same bathrooms VALUE; normalisation must stay finite.
        vectors = [
            encoded_apartment(100000, 1, 2),
            encoded_apartment(200000, 2, 2),
            encoded_apartment(300000, 3, 2),
        ]
        bounds, normalised = normalise_apartments(vectors)
        self.assertEqual(bounds["bathrooms"], (2.0, 2.0))
        for vector in normalised:
            self.assertEqual(vector["bathrooms"], 0.0)
            self.assertFalse(math.isnan(vector["bathrooms"]))

    def test_is_deterministic(self):
        vectors = [
            encoded_apartment(100000, 1, 1),
            encoded_apartment(300000, 3, 3),
        ]
        bounds_a, norm_a = normalise_apartments(vectors)
        bounds_b, norm_b = normalise_apartments(vectors)
        self.assertEqual(bounds_a, bounds_b)
        self.assertEqual(norm_a, norm_b)


class NormaliseTenantTests(django_tests.TestCase):
    def setUp(self):
        self.landlord = make_landlord()
        self.bounds = {"rental_price": (100000.0, 300000.0),
                       "bedrooms": (1.0, 3.0),
                       "bathrooms": (1.0, 3.0)}

    def test_tenant_numerical_preferences_normalised(self):
        tenant_vector = {
            "rental_price": 200000.0,
            "bedrooms": 2.0,
            "bathrooms": 1.0,
            **{c: 0 for c in one_hot_columns()},
            **{f: 0 for f in BINARY_FEATURES},
        }
        out = normalise_tenant_vector(tenant_vector, self.bounds)
        self.assertAlmostEqual(out["rental_price"], 0.5)
        self.assertAlmostEqual(out["bedrooms"], 0.5)
        self.assertAlmostEqual(out["bathrooms"], 0.0)

    def test_tenant_missing_values_preserved(self):
        from ml.preprocessing import encode_tenant_vector
        from apps.recommendations.models import Preference

        tenant = User.objects.create_user(
            email="tenant@example.com", password=PASSWORD,
            full_name="Tenant", role=User.Role.TENANT,
        )
        preference = Preference.objects.create(tenant=tenant, water=True)
        tenant_vector, _ = encode_tenant_vector(preference)
        out = normalise_tenant_vector(tenant_vector, self.bounds)
        self.assertIsNone(out["rental_price"])
        self.assertIsNone(out["bedrooms"])
        # Binary/categorical dimensions are untouched.
        self.assertEqual(out["water"], 1)

    def test_tenant_uses_apartment_bounds_for_common_frame(self):
        apartment = Apartment.objects.create(
            landlord=self.landlord, title="Flat", location="Calabar",
            rental_price="200000.00",
            apartment_type=Apartment.ApartmentType.TWO_BEDROOM,
            bedrooms=2, bathrooms=2,
        )
        a_vector = encode_apartment_vector(apartment)
        bounds = feature_bounds([a_vector])
        # An identical apartment query maps to the same normalised frame.
        self.assertEqual(bounds["rental_price"], (200000.0, 200000.0))


class NormaliseFeaturesDirectTests(django_tests.TestCase):
    """Direct unit coverage for ``normalise_features`` (Sprint 7.1).

    Verifies that only numerical features are rescaled while categorical
    (one-hot) and binary dimensions pass through unchanged, and that missing
    (``None``) values are preserved (AGENTS 14).
    """

    def setUp(self):
        self.bounds = {
            "rental_price": (100000.0, 300000.0),
            "bedrooms": (1.0, 3.0),
            "bathrooms": (1.0, 3.0),
        }

    def _vector(self, **overrides):
        vector = {
            "rental_price": 200000.0,
            "bedrooms": 2.0,
            "bathrooms": 2.0,
        }
        for column in one_hot_columns():
            vector[column] = 0
        vector["apartment_type_TWO_BEDROOM"] = 1
        binary = {feature: 0 for feature in BINARY_FEATURES}
        binary["parking"] = 1
        vector.update(binary)
        vector.update(overrides)
        return vector

    def test_numerical_features_are_rescaled(self):
        out = normalise_features(self._vector(), self.bounds)
        self.assertAlmostEqual(out["rental_price"], 0.5)
        self.assertAlmostEqual(out["bedrooms"], 0.5)
        self.assertAlmostEqual(out["bathrooms"], 0.5)

    def test_binary_and_categorical_dimensions_unchanged(self):
        out = normalise_features(self._vector(), self.bounds)
        self.assertEqual(out["parking"], 1)
        self.assertEqual(out["water"], 0)
        self.assertEqual(out["apartment_type_TWO_BEDROOM"], 1)
        self.assertEqual(out["apartment_type_ONE_BEDROOM"], 0)

    def test_divisor_zero_produces_zero_for_constant_feature(self):
        # Constant feature: lower == upper -> normalises to 0.0, not a crash.
        constant = dict(self.bounds)
        constant["bedrooms"] = (2.0, 2.0)
        out = normalise_features(self._vector(), constant)
        self.assertEqual(out["bedrooms"], 0.0)

    def test_missing_values_are_preserved(self):
        vector = self._vector(rental_price=None)
        out = normalise_features(vector, self.bounds)
        self.assertIsNone(out["rental_price"])

    def test_returns_a_copy_does_not_mutate_input(self):
        vector = self._vector()
        original = dict(vector)
        normalise_features(vector, self.bounds)
        self.assertEqual(vector, original)
