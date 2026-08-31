"""
ML evaluation for Phase 7, Sprint 7.6 - Weighted KNN Evaluation.

Sprint 7.6 (SYSTEM_REQUIREMENTS §41, §31) evaluates the Weighted KNN
recommendation component and produces the "ML evaluation results for Chapter
Four" deliverable. Earlier Phase 5 set a foundation this sprint builds on:

- the metrics and controlled catalogue live in ``ml.evaluation`` and
  ``ml.evaluation_scenarios`` and are already unit-tested;
- this suite runs the *real* engine (``ml.ranking.recommend`` /
  ``rank_recommendations``) against actual ``Apartment`` records and evaluates
  every Sprint 7.6 category with measured, reproducible outcomes.

Categories evaluated here:

- **recommendation relevance / metrics** - Precision@K, Recall@K, Hit Rate@K
  and NDCG@K computed from real engine output against a ground-truth relevance
  set (defined by the controlled ~tenant~ preference);
- **ranking correctness** - ascending weighted distance with consecutive 1-based
  ranks, and stability across repeated runs;
- **K behaviour** - the configured K is respected and reducing K returns the
  top-K nearest neighbours in the same relative order;
- **weighting behaviour** - increasing the weight of a feature directionally
  changes which candidate ranks first (a rank-flip sensitivity check);
- **response time** - the real pipeline is timed with ``time.perf_counter`` on
  a representative candidate set and the measured value is recorded, never
  fabricated (AGENTS 28, 40);
- **controlled preference scenarios** - a small set of deterministic scenarios
  with known expected ranking behaviour, all using clearly labelled evaluation
  data (AGENTS 40).
"""
import math
import time

import django.test as django_tests
from django.contrib.auth import get_user_model

from apps.apartments.models import Apartment
from apps.recommendations.models import Preference
from ml import evaluation
from ml.evaluation_scenarios import controlled_apartment_catalogue
from ml.features import DEFAULT_FEATURE_WEIGHTS, DEFAULT_K
from ml.ranking import rank_recommendations, recommend

User = get_user_model()
PASSWORD = "StrongPass123!"

# Generous single-run bound so a slow/CI runner is not flaky while any genuine
# slowdown still fails. The Sprint 7.4 API measurement was ~0.04s.
RESPONSE_TIME_BOUND_SECONDS = 2.0

# Catalogue identity is the 1-based position in the controlled catalogue.
_CATALOGUE_RELEVANT = {1, 2}


def _create_catalogue_apartments(landlord):
    """Seed real apartments from the controlled evaluation catalogue (AGENTS 40)."""
    catalogued = {}
    for index, spec in enumerate(
        controlled_apartment_catalogue()["candidates"], start=1
    ):
        catalogued[index] = Apartment.objects.create(
            landlord=landlord,
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
    return catalogued


class WeightedKnnEvaluationTests(django_tests.TestCase):
    """Category-level evaluation of the Weighted KNN engine over real data."""

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
        cls.apartments = _create_catalogue_apartments(cls.landlord)

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

    # ------------------------------------------------------------------ #
    # Recommendation relevance + metrics (controlled scenario)
    # ------------------------------------------------------------------ #

    def test_relevance_metrics_from_controlled_scenario(self):
        # Tenant who wants a Calabar 2-bed, 2-bath, furnished, secured flat
        # under N300k. Relax the facility hard filters so both relevant
        # catalogue candidates are eligible, then score the real ranking.
        preference = self._preference(security=None, furnished=None)
        results = recommend(Apartment.objects.all(), preference)
        relevant_pks = {
            self.apartments[index].pk for index in _CATALOGUE_RELEVANT
        }
        metrics = evaluation.evaluate(results, relevant_pks, k=len(results))
        for value in metrics.values():
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 1.0)
        # Both relevant furnished 2-bed flats are the only eligible candidates,
        # so every metric is perfect on this controlled scenario.
        self.assertEqual(metrics["precision"], 1.0)
        self.assertEqual(metrics["recall"], 1.0)
        self.assertEqual(metrics["hit_rate"], 1.0)
        self.assertAlmostEqual(metrics["ndcg"], 1.0)

    def test_precision_at_k_is_honest_when_not_all_retrieved_are_relevant(self):
        # Relax the type/bedroom/bathroom hard filters so the non-relevant
        # Calabar one-bedroom flat becomes eligible alongside the two relevant
        # furnished two-bed flats; the top-K then mixes relevant and
        # non-relevant items and Precision@K is strictly < 1 (never inflated).
        preference = self._preference(
            apartment_type=None,
            bedrooms=1,
            bathrooms=1,
            security=None,
            furnished=None,
        )
        results = recommend(Apartment.objects.all(), preference)
        relevant_pks = {
            self.apartments[index].pk for index in _CATALOGUE_RELEVANT
        }
        k = min(DEFAULT_K, len(results))
        precision = evaluation.precision_at_k(results, relevant_pks, k)
        self.assertGreaterEqual(precision, 0.0)
        self.assertLessEqual(precision, 1.0)
        # At least one non-relevant flat sits in the top-K, so precision is below
        # 1.0 - the metric reflects the real composition of the ranking.
        self.assertLess(precision, 1.0)

    # ------------------------------------------------------------------ #
    # Ranking correctness
    # ------------------------------------------------------------------ #

    def test_ranking_is_ascending_by_distance_with_consecutive_ranks(self):
        preference = self._preference(security=None, furnished=None)
        results = recommend(Apartment.objects.all(), preference)
        self.assertGreaterEqual(len(results), 1)
        distances = [r["distance"] for r in results]
        self.assertEqual(distances, sorted(distances))
        for rank, result in enumerate(results, start=1):
            self.assertEqual(result["rank"], rank)

    def test_weighted_distance_and_similarity_are_consistent(self):
        preference = self._preference(security=None, furnished=None)
        results = recommend(Apartment.objects.all(), preference)
        for result in results:
            self.assertIsInstance(result["distance"], float)
            self.assertGreaterEqual(result["distance"], 0.0)
            self.assertAlmostEqual(result["similarity"], math.exp(-result["distance"]))

    def test_ranking_is_reproducible(self):
        preference = self._preference(security=None, furnished=None)
        first = recommend(Apartment.objects.all(), preference)
        second = recommend(Apartment.objects.all(), preference)
        for a, b in zip(first, second):
            self.assertEqual(a["apartment"].pk, b["apartment"].pk)
            self.assertEqual(a["distance"], b["distance"])
            self.assertEqual(a["rank"], b["rank"])

    # ------------------------------------------------------------------ #
    # K behaviour
    # ------------------------------------------------------------------ #

    def test_k_behaviour_larger_k_returns_more_neighbours(self):
        # A dedicated scenario (distinct location) with many eligible Calabar
        # flats so K is genuinely binding.
        for index in range(9):
            Apartment.objects.create(
                landlord=self.landlord,
                title=f"K-Neighbour Flat {index}",
                location="K-Town",
                rental_price=f"{150000 + index * 10000}.00",
                apartment_type=Apartment.ApartmentType.FLAT,
                bedrooms=2,
                bathrooms=2,
                security=True,
                furnished=index % 2 == 0,
                availability=True,
            )
        # No type/facility hard filters: location + generous price cap only.
        preference = self._preference(
            location="K-Town",
            max_rent="500000.00",
            apartment_type=None,
            bedrooms=None,
            bathrooms=None,
            security=None,
            furnished=None,
        )
        full = recommend(Apartment.objects.all(), preference)
        # 9 eligible neighbours > DEFAULT_K -> exactly DEFAULT_K returned.
        self.assertEqual(len(full), DEFAULT_K)
        # Requesting fewer neighbours (3) returns exactly the top 3.
        fewer = recommend(Apartment.objects.all(), preference, k=3)
        self.assertEqual(len(fewer), 3)
        # The 3-neighbour ranking is the prefix of the full ranking (same order).
        full_pks = [r["apartment"].pk for r in full]
        fewer_pks = [r["apartment"].pk for r in fewer]
        self.assertEqual(fewer_pks, full_pks[:3])

    # ------------------------------------------------------------------ #
    # Weighting behaviour (directional rank flip)
    # ------------------------------------------------------------------ #

    def test_weighting_directionally_changes_ranking(self):
        # Two candidates identical in every feature except bedrooms & parking.
        # Candidate A matches preferred bedrooms but lacks parking; candidate B
        # matches parking but has the wrong bedroom count.
        base = dict(
            landlord=self.landlord,
            location="Calabar",
            rental_price="250000.00",
            apartment_type=Apartment.ApartmentType.TWO_BEDROOM,
            bathrooms=2,
            security=True,
            electricity=True,
            water=True,
            furnished=True,
            availability=True,
        )
        a = Apartment.objects.create(**{**base, "title": "A bedroom-match",
                                        "bedrooms": 3, "parking": False})
        b = Apartment.objects.create(**{**base, "title": "B parking-match",
                                        "bedrooms": 1, "parking": True})

        # Preference cares only about bedrooms (3) and parking (True); every
        # other preference dimension is unstated so only those two contribute.
        preference = self._preference(
            bedrooms=3, parking=True,
            bathrooms=None, furnished=None, security=None,
        )

        # Default weights prioritise bedrooms (2.0) over parking (1.0) -> the
        # bedroom-matching candidate A ranks first.
        default = rank_recommendations([a, b], preference)
        self.assertEqual(default[0]["apartment"].pk, a.pk)

        # Elevate parking (5.0) and de-emphasise bedrooms (0.5) -> the
        # parking-matching candidate B ranks first (rank flip).
        heavy_parking = dict(DEFAULT_FEATURE_WEIGHTS)
        heavy_parking["bedrooms"] = 0.5
        heavy_parking["parking"] = 5.0
        flipped = rank_recommendations([a, b], preference, weights=heavy_parking)
        self.assertEqual(flipped[0]["apartment"].pk, b.pk)

        # The two runs genuinely differ: their top-ranked candidates are not the
        # same, proving the weight change altered the ranking directionally.
        self.assertNotEqual(
            default[0]["apartment"].pk, flipped[0]["apartment"].pk
        )

    # ------------------------------------------------------------------ #
    # Response time (measured, never fabricated - AGENTS 28, 40)
    # ------------------------------------------------------------------ #

    def test_recommendation_engine_response_time(self):
        # Seed a representative candidate set (30 apartments) and time the whole
        # pipeline end to end through the real engine.
        for index in range(30):
            Apartment.objects.create(
                landlord=self.landlord,
                title=f"Timed Flat {index}",
                location="Calabar" if index % 2 == 0 else "Uyo",
                rental_price=f"{150000 + index * 5000}.00",
                apartment_type=Apartment.ApartmentType.FLAT,
                bedrooms=2,
                bathrooms=2,
                security=True,
                furnished=index % 3 == 0,
                availability=True,
            )
        preference = self._preference(furnished=None)
        start = time.perf_counter()
        results = recommend(Apartment.objects.all(), preference)
        elapsed = time.perf_counter() - start

        self.assertGreaterEqual(len(results), 1)
        self.assertLess(elapsed, RESPONSE_TIME_BOUND_SECONDS)
        # Recorded (real) measurement surfaced for the sprint report.
        print(f"\nSprint7.6 measured engine response time = {elapsed:.4f}s")

    # ------------------------------------------------------------------ #
    # Controlled preference scenarios (AGENTS 40 - labelled evaluation data)
    # ------------------------------------------------------------------ #

    def test_controlled_scenario_facility_preference_changes_eligibility(self):
        # When the tenant requires furnished + secured, only the relevant
        # furnished/secured Calabar candidates stay eligible (hard filters).
        preference = self._preference(security=True, furnished=True)
        results = recommend(Apartment.objects.all(), preference)
        for result in results:
            self.assertTrue(result["apartment"].furnished)
            self.assertTrue(result["apartment"].security)
            self.assertEqual(result["apartment"].location, "Calabar")
            self.assertLessEqual(result["apartment"].rental_price, 300000)

    def test_controlled_scenario_price_cap_is_a_hard_constraint(self):
        # A tenant whose max rent is N200k must never receive the N250k+
        # catalogue flats, even if they are otherwise similar (AGENTS 15).
        preference = self._preference(max_rent="200000.00", security=None)
        results = recommend(Apartment.objects.all(), preference)
        self.assertGreaterEqual(len(results), 1)
        for result in results:
            self.assertLessEqual(result["apartment"].rental_price, 200000)
