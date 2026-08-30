"""
Unit tests for Phase 5, Sprint 5.6 - Recommendation service layer.

These verify the service that runs the Weighted KNN engine and persists the
results: a ``Recommendation`` with ranked ``RecommendationItem`` rows, correct
K and algorithm, the no-preference / wrong-owner errors, and the empty-result
(capable of zero items) behaviour.
"""
import django.test as django_tests
from django.contrib.auth import get_user_model

from apps.apartments.models import Apartment
from apps.recommendations.models import Preference, Recommendation, RecommendationItem
from apps.recommendations.services import (
    NoPreferenceError,
    generate_recommendations,
)

User = get_user_model()
PASSWORD = "StrongPass123!"


def make_user(email, role):
    return User.objects.create_user(
        email=email, password=PASSWORD, full_name="User", role=role
    )


class RecommendationServiceTests(django_tests.TestCase):
    def setUp(self):
        self.tenant = make_user("tenant@example.com", User.Role.TENANT)
        self.landlord = make_user("landlord@example.com", User.Role.LANDLORD)
        self.apartments = [
            Apartment.objects.create(
                landlord=self.landlord,
                title=f"Flat {price}",
                location="Calabar",
                rental_price=price,
                apartment_type=Apartment.ApartmentType.TWO_BEDROOM,
                bedrooms=2,
                bathrooms=2,
            )
            for price in ("180000.00", "250000.00", "300000.00")
        ]

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

    def test_generates_and_persists_ranked_items(self):
        preference = self._preference()
        recommendation = generate_recommendations(self.tenant, preference)

        self.assertEqual(Recommendation.objects.count(), 1)
        self.assertEqual(RecommendationItem.objects.count(), 3)

        recommendation.refresh_from_db()
        self.assertEqual(recommendation.algorithm, "weighted_knn")
        self.assertEqual(recommendation.preference, preference)
        self.assertEqual(recommendation.tenant, self.tenant)

        # Ranked ascending by distance; distance non-negative and ordered.
        items = list(recommendation.items.all())
        self.assertEqual([item.rank for item in items], [1, 2, 3])
        self.assertLessEqual(items[0].distance, items[1].distance)
        self.assertLessEqual(items[1].distance, items[2].distance)

    def test_recommendation_k_is_configurable_constant(self):
        from ml.features import DEFAULT_K

        recommendation = generate_recommendations(self.tenant, self._preference())
        self.assertEqual(recommendation.k, DEFAULT_K)

    def test_no_preference_raises(self):
        with self.assertRaises(NoPreferenceError):
            generate_recommendations(self.tenant, None)

    def test_foreign_preference_raises(self):
        other_tenant = make_user("other@example.com", User.Role.TENANT)
        preference = Preference.objects.create(tenant=other_tenant)
        with self.assertRaises(NoPreferenceError):
            generate_recommendations(self.tenant, preference)

    def test_no_eligible_candidates_persists_empty_run(self):
        # No apartment is available in Calabar below max_rent -> zeros.
        for apartment in self.apartments:
            apartment.availability = False
            apartment.save()
        recommendation = generate_recommendations(self.tenant, self._preference())
        self.assertEqual(recommendation.items.count(), 0)

    def test_each_new_run_is_a_fresh_record(self):
        preference = self._preference()
        first = generate_recommendations(self.tenant, preference)
        second = generate_recommendations(self.tenant, preference)
        self.assertNotEqual(first.pk, second.pk)