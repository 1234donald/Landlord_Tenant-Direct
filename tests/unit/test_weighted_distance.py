"""
Unit tests for Phase 5, Sprint 5.4 - Feature weighting and weighted distance.

These verify the weighted-distance engine deliverable in ``ml.weighted_knn``:
weight configuration (defaults and validated overrides), the weighted
Euclidean distance Dw(U,A) = sqrt(Σ wi(ui-ai)²), and the active-mask
neutralisation of unstated preferences. Known numerical cases with expected
distances are included to validate mathematical correctness (AGENTS 27).
"""
import math

import django.test as django_tests
from django.contrib.auth import get_user_model

from apps.apartments.models import Apartment
from ml.features import DEFAULT_FEATURE_WEIGHTS, FEATURE_NAMES
from ml.preprocessing import (
    encode_apartment_vector,
    encode_tenant_vector,
    one_hot_columns,
)
from ml.weighted_knn import (
    resolve_weights,
    similarity,
    weighted_distance,
)

User = get_user_model()
PASSWORD = "StrongPass123!"


def full_weights(**changes):
    """A complete, valid weight mapping (defaults plus any overrides)."""
    weights = dict(DEFAULT_FEATURE_WEIGHTS)
    weights.update(changes)
    return weights


class ResolveWeightsTests(django_tests.TestCase):
    def test_none_returns_defaults(self):
        self.assertEqual(resolve_weights(None), DEFAULT_FEATURE_WEIGHTS)

    def test_none_returns_a_copy(self):
        self.assertIsNot(resolve_weights(None), DEFAULT_FEATURE_WEIGHTS)

    def test_rejects_incomplete_weights(self):
        with self.assertRaises(ValueError):
            resolve_weights({"rental_price": 2.0})

    def test_rejects_negative_weight(self):
        weights = full_weights(parking=-1)
        with self.assertRaises(ValueError):
            resolve_weights(weights)

    def test_accepts_complete_override(self):
        weights = full_weights(rental_price=4.0)
        self.assertEqual(resolve_weights(weights)["rental_price"], 4.0)


class WeightedDistanceKnownCasesTests(django_tests.TestCase):
    def test_identical_vectors_give_zero(self):
        vector = {"rental_price": 0.5, "bedrooms": 2.0}
        self.assertEqual(weighted_distance(vector, dict(vector)), 0.0)

    def test_single_dimension_known_value(self):
        # Default weight for rental_price is 3.0, diff = 0.25.
        d = weighted_distance({"rental_price": 0.5}, {"rental_price": 0.25})
        expected = math.sqrt(3.0 * (0.5 - 0.25) ** 2)
        self.assertAlmostEqual(d, expected, places=6)
        self.assertAlmostEqual(d, 0.4330127, places=5)

    def test_custom_weight_changes_distance(self):
        # rental_price weight 4.0, diff = 1.0 -> sqrt(4) = 2.0.
        weights = full_weights(rental_price=4.0)
        d = weighted_distance({"rental_price": 1.0}, {"rental_price": 0.0}, weights=weights)
        self.assertAlmostEqual(d, 2.0, places=6)

    def test_unstated_dimension_is_neutralised(self):
        # parking is far apart but inactive -> contributes nothing.
        tenant = {"rental_price": 1.0, "parking": 1.0}
        apartment = {"rental_price": 1.0, "parking": 0.0}
        mask = {"rental_price": True, "parking": False}
        self.assertEqual(weighted_distance(tenant, apartment, active_mask=mask), 0.0)

    def test_none_tenant_value_is_ignored_even_without_mask(self):
        tenant = {"rental_price": None, "parking": 1.0}
        apartment = {"rental_price": 5.0, "parking": 1.0}
        self.assertEqual(weighted_distance(tenant, apartment), 0.0)

    def test_missing_apartment_dimension_is_skipped(self):
        tenant = {"rental_price": 1.0}
        apartment = {"rental_price": 0.5, "parking": 0.0}
        d = weighted_distance(tenant, apartment)
        expected = math.sqrt(3.0 * (1.0 - 0.5) ** 2)
        self.assertAlmostEqual(d, expected, places=6)


class CategoricalTypeTests(django_tests.TestCase):
    def test_matching_type_contributes_zero(self):
        tenant = {"apartment_type_TWO_BEDROOM": 1, "rental_price": 0.5}
        apartment = {"apartment_type_TWO_BEDROOM": 1, "rental_price": 0.5}
        self.assertEqual(weighted_distance(tenant, apartment), 0.0)

    def test_mismatched_type_contributes_type_weight(self):
        # Tenant wants TWO_BEDROOM (its column 1); apartment is another type
        # (column 0). diff = 1 on the active column; base weight 2.0.
        d = weighted_distance(
            {"apartment_type_TWO_BEDROOM": 1},
            {"apartment_type_TWO_BEDROOM": 0},
        )
        self.assertAlmostEqual(d, math.sqrt(2.0), places=6)

    def test_no_type_preference_contributes_nothing(self):
        # All type columns inactive -> no contribution regardless of apartment.
        tenant = {}
        apartment = {col: 0 for col in one_hot_columns()}
        self.assertEqual(weighted_distance(tenant, apartment), 0.0)


class SimilarityTests(django_tests.TestCase):
    def test_perfect_match_similarity_is_one(self):
        vector = {"rental_price": 0.5}
        self.assertEqual(similarity(vector, dict(vector)), 1.0)

    def test_similarity_is_between_zero_and_one(self):
        s = similarity({"rental_price": 1.0}, {"rental_price": 0.0})
        expected = math.exp(-math.sqrt(3.0))
        self.assertAlmostEqual(s, expected, places=6)
        self.assertGreater(s, 0.0)
        self.assertLess(s, 1.0)

    def test_similarity_monotonic_in_distance(self):
        close = similarity({"rental_price": 0.9}, {"rental_price": 1.0})
        far = similarity({"rental_price": 0.1}, {"rental_price": 1.0})
        self.assertGreater(close, far)


class PipelineIntegrationTests(django_tests.TestCase):
    def setUp(self):
        self.landlord = User.objects.create_user(
            email="landlord@example.com", password=PASSWORD,
            full_name="Landlord", role=User.Role.LANDLORD,
        )
        self.tenant = User.objects.create_user(
            email="tenant@example.com", password=PASSWORD,
            full_name="Tenant", role=User.Role.TENANT,
        )

    def _apartment(self, price, apartment_type, bedrooms, bathrooms):
        return Apartment.objects.create(
            landlord=self.landlord, title="Flat", location="Calabar",
            rental_price=price, apartment_type=apartment_type,
            bedrooms=bedrooms, bathrooms=bathrooms,
        )

    def test_distance_is_finite_and_orders_matches(self):
        from apps.recommendations.models import Preference

        matching = self._apartment(
            "200000.00", Apartment.ApartmentType.TWO_BEDROOM, 2, 2
        )
        distant = self._apartment(
            "1000000.00", Apartment.ApartmentType.DUPLEX, 4, 3
        )
        preference = Preference.objects.create(
            tenant=self.tenant, max_rent="250000.00",
            apartment_type=Apartment.ApartmentType.TWO_BEDROOM,
            bedrooms=2, bathrooms=2,
        )
        tenant_vector, active_mask = encode_tenant_vector(preference)
        a_match = encode_apartment_vector(matching)
        a_distant = encode_apartment_vector(distant)

        d_match = weighted_distance(tenant_vector, a_match, active_mask=active_mask)
        d_distant = weighted_distance(tenant_vector, a_distant, active_mask=active_mask)

        self.assertTrue(math.isfinite(d_match))
        self.assertTrue(math.isfinite(d_distant))
        self.assertGreaterEqual(d_match, 0.0)
        self.assertLess(d_match, d_distant)
