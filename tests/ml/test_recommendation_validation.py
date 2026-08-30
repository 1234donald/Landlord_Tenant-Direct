"""
ML tests for Phase 5, Sprint 5.7 - recommendation validation and evaluation
readiness.

These run the real Weighted KNN ranking engine (``ml.ranking.recommend``)
against actual ``Apartment`` records seeded from the reproducible controlled
catalogue (``ml.evaluation_scenarios``), then verify the Phase 5 exit criteria
(SYSTEM_REQUIREMENTS §40 / Sprint 5.7):

- actual apartment records are ranked (not placeholders);
- no fake recommendation scores are used (distance & similarity are real and
  consistent);
- lower weighted distance results in higher ranking;
- the algorithm is reproducible;
- hard filters, K configuration and missing-data handling behave correctly;
- evaluation metrics can be computed against a ground-truth relevance set.
"""
import math

import django.test as django_tests
from django.contrib.auth import get_user_model

from apps.apartments.models import Apartment
from apps.recommendations.models import Preference
from ml import evaluation
from ml.evaluation_scenarios import controlled_apartment_catalogue
from ml.features import DEFAULT_K
from ml.ranking import recommend

User = get_user_model()
PASSWORD = "StrongPass123!"

# The catalogue's identity is the 1-based position in the candidate list.
_RELEVANT = {1, 2}


class RecommendationValidationTests(django_tests.TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.landlord = User.objects.create_user(
            email="landlord@example.com",
            password=PASSWORD,
            full_name="Landlord",
            role=User.Role.LANDLORD,
        )
        cls.tenant = User.objects.create_user(
            email="tenant@example.com",
            password=PASSWORD,
            full_name="Tenant",
            role=User.Role.TENANT,
        )
        catalogue = controlled_apartment_catalogue()
        cls.apartments = {}
        for index, spec in enumerate(catalogue["candidates"], start=1):
            cls.apartments[index] = Apartment.objects.create(
                landlord=cls.landlord,
                title=spec["title"],
                location=spec["location"],
                rental_price=spec["rental_price"],
                apartment_type=Apartment.ApartmentType(spec["apartment_type"]),
                bedrooms=spec["bedrooms"],
                bathrooms=spec["bathrooms"],
                parking=spec["parking"],
                electricity=spec["electricity"],
                water=spec["water"],
                security=spec["security"],
                furnished=spec["furnished"],
                availability=True,
            )

    def _preference(self, **overrides):
        params = dict(
            tenant=self.tenant,
            location="Calabar",
            max_rent="300000.00",
            apartment_type=Apartment.ApartmentType.TWO_BEDROOM,
            bedrooms=2,
            bathrooms=2,
            security=True,
            furnished=True,
        )
        params.update(overrides)
        return Preference.objects.create(**params)

    def _results(self, **preference_overrides):
        preference = self._preference(**preference_overrides)
        return recommend(Apartment.objects.all(), preference)

    def test_actual_records_are_ranked(self):
        results = self._results()
        self.assertGreater(len(results), 0)
        apartment_pks = {self.apartments[i].pk for i in range(1, 6)}
        for result in results:
            self.assertIn(result["apartment"].pk, apartment_pks)

    def test_lower_distance_results_in_higher_ranking(self):
        results = self._results()
        distances = [r["distance"] for r in results]
        self.assertEqual(
            distances, sorted(distances), "ranking must be ascending by distance"
        )
        for rank, result in enumerate(results, start=1):
            self.assertEqual(result["rank"], rank)

    def test_no_fake_scores_are_used(self):
        results = self._results()
        for result in results:
            distance = result["distance"]
            self.assertIsInstance(distance, float)
            self.assertGreaterEqual(distance, 0.0)
            # similarity must be exactly the engine's exp(-distance) transform.
            self.assertAlmostEqual(result["similarity"], math.exp(-distance))

    def test_recommendation_is_reproducible(self):
        preference = self._preference()
        first = recommend(Apartment.objects.all(), preference)
        second = recommend(Apartment.objects.all(), preference)
        for a, b in zip(first, second):
            self.assertEqual(a["apartment"].pk, b["apartment"].pk)
            self.assertEqual(a["distance"], b["distance"])
            self.assertEqual(a["rank"], b["rank"])

    def test_hard_filters_exclude_non_compliant_apartments(self):
        # Two-bed Calabar under max_rent, secured & furnished -> only the two
        # relevant furnished candidates survive the hard filters.
        results = self._results()
        for result in results:
            self.assertLessEqual(result["apartment"].rental_price, 300000)
            self.assertEqual(result["apartment"].location, "Calabar")
            self.assertTrue(result["apartment"].furnished)
            self.assertTrue(result["apartment"].security)

    def test_k_respects_configuration_and_available_candidates(self):
        results = self._results()
        # Only 1 candidate passes the strict (furnished + secured) hard filters,
        # which is well below DEFAULT_K -> all eligible candidates are returned.
        self.assertLessEqual(len(results), DEFAULT_K)
        self.assertEqual(len(results), 1)

    def test_missing_data_handling_none_facility_imposes_no_constraint(self):
        # A preference with facility=None must not filter those apartments out;
        # with furnished unstated, both the furnished and unfurnished Calabar
        # 2-bed flats become eligible (2 candidates).
        results = self._results(security=None, furnished=None)
        self.assertEqual(len(results), 2)

    def test_evaluation_metrics_computed_from_actual_ranking(self):
        # Compare the real engine output against the known-relevant 2-bed flats
        # under a relaxed (facility unstated) preference so both are eligible.
        results = self._results(security=None, furnished=None)
        relevant_pks = {self.apartments[index].pk for index in _RELEVANT}
        metrics = evaluation.evaluate(results, relevant_pks, k=len(results))
        for value in metrics.values():
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 1.0)
        # Both relevant 2-bed flats rank inside the (2-item) result set, so the
        # evaluated metrics are all perfect here.
        self.assertEqual(metrics["precision"], 1.0)
        self.assertEqual(metrics["recall"], 1.0)
        self.assertEqual(metrics["hit_rate"], 1.0)
        self.assertAlmostEqual(metrics["ndcg"], 1.0)
