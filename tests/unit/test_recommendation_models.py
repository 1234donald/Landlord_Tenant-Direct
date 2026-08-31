"""
Unit tests for Phase 7, Sprint 7.1 - Recommendation models.

This module adds direct unit coverage for the ``Recommendation`` and
``RecommendationItem`` models, which were previously exercised only indirectly
through service tests. It verifies the tenant/preference relationships, the
algorithm and K fields, string representation, ordering, the declared index and
the unique (recommendation, apartment) constraint (SYSTEM_REQUIREMENTS 41).
"""
import django.test as django_tests
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from apps.apartments.models import Apartment
from apps.recommendations.models import (
    Preference,
    Recommendation,
    RecommendationItem,
)
from ml.features import DEFAULT_K

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


class RecommendationModelTests(django_tests.TestCase):
    def setUp(self):
        self.tenant = make_tenant()
        self.preference = Preference.objects.create(
            tenant=self.tenant, location="Calabar"
        )

    def test_recommendation_relation_to_tenant_and_preference(self):
        recommendation = Recommendation.objects.create(
            tenant=self.tenant,
            preference=self.preference,
        )
        self.assertEqual(recommendation.tenant, self.tenant)
        self.assertEqual(recommendation.preference, self.preference)
        self.assertIn(recommendation, self.tenant.recommendations.all())
        self.assertIn(recommendation, self.preference.recommendations.all())

    def test_default_algorithm_and_k(self):
        recommendation = Recommendation.objects.create(
            tenant=self.tenant, preference=self.preference
        )
        self.assertEqual(
            recommendation.algorithm, Recommendation.Algorithm.WEIGHTED_KNN
        )
        self.assertEqual(recommendation.k, DEFAULT_K)

    def test_algorithm_choice(self):
        self.assertEqual(
            set(Recommendation.Algorithm.values), {"weighted_knn"}
        )

    def test_created_at_populated(self):
        recommendation = Recommendation.objects.create(
            tenant=self.tenant, preference=self.preference
        )
        self.assertIsNotNone(recommendation.created_at)

    def test_string_representation(self):
        recommendation = Recommendation.objects.create(
            tenant=self.tenant, preference=self.preference
        )
        self.assertIn("Recommendation for tenant", str(recommendation))

    def test_preference_set_null_when_preference_deleted(self):
        recommendation = Recommendation.objects.create(
            tenant=self.tenant, preference=self.preference
        )
        self.preference.delete()
        recommendation.refresh_from_db()
        self.assertIsNone(recommendation.preference)

    def test_recommendation_deleted_when_tenant_deleted(self):
        recommendation = Recommendation.objects.create(
            tenant=self.tenant, preference=self.preference
        )
        pk = recommendation.pk
        self.tenant.delete()
        self.assertFalse(Recommendation.objects.filter(pk=pk).exists())

    def test_declared_indexes_on_tenant_and_preference(self):
        index_fields = {
            tuple(index.fields) for index in Recommendation._meta.indexes
        }
        self.assertIn(("tenant",), index_fields)
        self.assertIn(("preference",), index_fields)


class RecommendationItemModelTests(django_tests.TestCase):
    def setUp(self):
        self.landlord = make_landlord()
        self.tenant = make_tenant()
        self.preference = Preference.objects.create(
            tenant=self.tenant, location="Calabar"
        )
        self.recommendation = Recommendation.objects.create(
            tenant=self.tenant, preference=self.preference
        )
        self.apartment_a = Apartment.objects.create(
            landlord=self.landlord,
            title="Flat A",
            location="Calabar",
            rental_price="200000.00",
            apartment_type=Apartment.ApartmentType.TWO_BEDROOM,
            bedrooms=2,
            bathrooms=2,
        )
        self.apartment_b = Apartment.objects.create(
            landlord=self.landlord,
            title="Flat B",
            location="Calabar",
            rental_price="150000.00",
            apartment_type=Apartment.ApartmentType.ONE_BEDROOM,
            bedrooms=1,
            bathrooms=1,
        )

    def _item(self, apartment, rank=1):
        return RecommendationItem.objects.create(
            recommendation=self.recommendation,
            apartment=apartment,
            rank=rank,
            distance=0.5,
            similarity=0.6,
        )

    def test_item_relationships(self):
        item = self._item(self.apartment_a)
        self.assertEqual(item.recommendation, self.recommendation)
        self.assertEqual(item.apartment, self.apartment_a)
        self.assertIn(item, self.recommendation.items.all())

    def test_unique_constraint_on_recommendation_and_apartment(self):
        self._item(self.apartment_a, rank=1)
        with self.assertRaises(IntegrityError):
            RecommendationItem.objects.create(
                recommendation=self.recommendation,
                apartment=self.apartment_a,
                rank=2,
                distance=0.1,
                similarity=0.9,
            )

    def test_same_apartment_allowed_in_different_recommendations(self):
        self._item(self.apartment_a, rank=1)
        other_recommendation = Recommendation.objects.create(
            tenant=self.tenant, preference=self.preference
        )
        RecommendationItem.objects.create(
            recommendation=other_recommendation,
            apartment=self.apartment_a,
            rank=1,
            distance=0.5,
            similarity=0.6,
        )
        self.assertEqual(
            RecommendationItem.objects.filter(apartment=self.apartment_a).count(),
            2,
        )

    def test_rank_distance_similarity_fields_are_stored(self):
        item = self._item(self.apartment_a, rank=3)
        item.distance = 1.25
        item.similarity = 0.29
        item.save()
        item.refresh_from_db()
        self.assertEqual(item.rank, 3)
        self.assertEqual(item.distance, 1.25)
        self.assertAlmostEqual(item.similarity, 0.29)

    def test_item_cascade_deletes_with_recommendation(self):
        item = self._item(self.apartment_a)
        pk = item.pk
        self.recommendation.delete()
        self.assertFalse(RecommendationItem.objects.filter(pk=pk).exists())

    def test_item_cascade_deletes_with_apartment(self):
        item = self._item(self.apartment_a)
        pk = item.pk
        self.apartment_a.delete()
        self.assertFalse(RecommendationItem.objects.filter(pk=pk).exists())

    def test_default_ordering_by_recommendation_then_rank(self):
        first = self._item(self.apartment_a, rank=1)
        second = self._item(self.apartment_b, rank=2)
        self.assertEqual(
            list(self.recommendation.items.all()), [first, second]
        )

    def test_string_representation(self):
        item = self._item(self.apartment_a, rank=4)
        self.assertIn("Rank 4", str(item))
