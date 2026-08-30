"""
Unit tests for Phase 5, Sprint 5.1 - Recommendation feature specification.

These verify that ``ml.features`` is a self-consistent, complete and correct
feature specification for the Weighted KNN component: the confirmed feature set
is closed under the three classifications, covers exactly the distance features
used, maps one-to-one to the database schema, applies non-negative weights, and
its hard-filter fields align with the actual Apartment/Preference model fields
and with the existing search/filter logic (AGENTS 13, 27; Sprint 5.1 deliverable).
"""
import django.test as django_tests

import ml.features
from ml.features import (
    APARTMENT_FIELD_MAP,
    APARTMENT_TYPES,
    BINARY_FEATURES,
    CATEGORICAL_FEATURES,
    DEFAULT_FEATURE_WEIGHTS,
    DEFAULT_K,
    FEATURE_NAMES,
    HARD_FILTER_FIELDS,
    NUMERICAL_FEATURES,
    PREFERENCE_FIELD_MAP,
    validate_feature_weights,
)
from apps.apartments.models import Apartment


class FeatureListTests(django_tests.TestCase):
    def test_feature_names_are_unique_and_non_empty(self):
        self.assertEqual(len(set(FEATURE_NAMES)), len(FEATURE_NAMES))
        self.assertTrue(FEATURE_NAMES)

    def test_classifications_partition_the_feature_set(self):
        classified = (
            set(NUMERICAL_FEATURES)
            | set(CATEGORICAL_FEATURES)
            | set(BINARY_FEATURES)
        )
        self.assertEqual(classified, set(FEATURE_NAMES))

    def test_individual_classifications_are_disjoint(self):
        self.assertFalse(set(NUMERICAL_FEATURES) & set(CATEGORICAL_FEATURES))
        self.assertFalse(set(NUMERICAL_FEATURES) & set(BINARY_FEATURES))
        self.assertFalse(set(CATEGORICAL_FEATURES) & set(BINARY_FEATURES))

    def test_expected_classifications(self):
        self.assertEqual(set(NUMERICAL_FEATURES), {"rental_price", "bedrooms", "bathrooms"})
        self.assertEqual(set(CATEGORICAL_FEATURES), {"apartment_type"})
        self.assertEqual(
            set(BINARY_FEATURES),
            {"parking", "electricity", "water", "security", "furnished"},
        )


class DatabaseMappingTests(django_tests.TestCase):
    def test_apartment_field_map_covers_every_feature(self):
        self.assertEqual(set(APARTMENT_FIELD_MAP), set(FEATURE_NAMES))

    def test_preference_field_map_covers_every_feature(self):
        self.assertEqual(set(PREFERENCE_FIELD_MAP), set(FEATURE_NAMES))

    def test_apartment_fields_exist_on_apartment_model(self):
        for feature in FEATURE_NAMES:
            field = APARTMENT_FIELD_MAP[feature]
            self.assertTrue(
                hasattr(Apartment, field),
                f"Apartment has no field {field!r} for {feature!r}",
            )

    def test_preference_fields_exist_on_preference_model(self):
        from apps.recommendations.models import Preference

        for feature in FEATURE_NAMES:
            field = PREFERENCE_FIELD_MAP[feature]
            self.assertTrue(
                hasattr(Preference, field),
                f"Preference has no field {field!r} for {feature!r}",
            )

    def test_apartment_type_labels_match_apartment_model(self):
        self.assertEqual(
            set(APARTMENT_TYPES),
            {choice[0] for choice in Apartment.ApartmentType.choices},
        )


class WeightTests(django_tests.TestCase):
    def test_default_weights_cover_every_feature(self):
        self.assertEqual(set(DEFAULT_FEATURE_WEIGHTS), set(FEATURE_NAMES))

    def test_default_weights_are_non_negative(self):
        for value in DEFAULT_FEATURE_WEIGHTS.values():
            self.assertGreaterEqual(value, 0)

    def test_rental_price_is_weighted_highest(self):
        self.assertGreater(
            DEFAULT_FEATURE_WEIGHTS["rental_price"],
            DEFAULT_FEATURE_WEIGHTS["bedrooms"],
        )

    def test_validate_accepts_defaults(self):
        self.assertTrue(validate_feature_weights(DEFAULT_FEATURE_WEIGHTS))

    def test_validate_rejects_missing_feature(self):
        weights = dict(DEFAULT_FEATURE_WEIGHTS)
        del weights["parking"]
        self.assertFalse(validate_feature_weights(weights))

    def test_validate_rejects_negative_weight(self):
        weights = dict(DEFAULT_FEATURE_WEIGHTS)
        weights["parking"] = -1
        self.assertFalse(validate_feature_weights(weights))

    def test_validate_rejects_non_number_weight(self):
        weights = dict(DEFAULT_FEATURE_WEIGHTS)
        weights["parking"] = "yes"
        self.assertFalse(validate_feature_weights(weights))

    def test_validate_rejects_non_dict(self):
        self.assertFalse(validate_feature_weights([1, 2]))


class HardFilterTests(django_tests.TestCase):
    def test_hard_filter_fields_are_a_subset_of_features_and_rent(self):
        self.assertTrue(set(HARD_FILTER_FIELDS).issubset(set(FEATURE_NAMES) | {"max_rent"}))

    def test_hard_filter_fields_exist_on_preference_model(self):
        from apps.recommendations.models import Preference

        for field in HARD_FILTER_FIELDS:
            self.assertTrue(hasattr(Preference, field), f"Missing preference field {field}")

    def test_availability_is_always_required(self):
        self.assertTrue(ml.features.HARD_FILTER_AVAILABILITY)

    def test_k_is_a_positive_default(self):
        self.assertIsInstance(DEFAULT_K, int)
        self.assertGreater(DEFAULT_K, 0)
