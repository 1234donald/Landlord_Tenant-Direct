"""
Formal Weighted KNN evaluation (Chapter Four evidence).

This suite performs the documented, reproducible evaluation of the Weighted
KNN recommendation component for Chapter Four. It pairs the Sprint 7.6
validation suite (``test_weighted_knn_evaluation.py``) with a *formal*,
multi-case measurement over a larger deterministic catalogue:

- evaluation data: ``formal_evaluation_catalogue`` (32 clearly-labelled
  synthetic apartments, AGENTS 40) from ``ml.evaluation_scenarios``;
- ground truth: the independent, documented ``relevance_indices`` rule —
  relevance is derived from the tenant's stated core requirements, never from
  the KNN distances;
- engine: the *real* ``ml.ranking.recommend`` / ``hard_filter_queryset``;
- metrics: the real ``ml.evaluation`` functions (Precision@K, Recall@K,
  Hit Rate@K, NDCG@K).

Constraints honoured (AGENTS 17, 28, 40, 41): every figure is computed by
actually executing the implemented engine; nothing is fabricated; weight and K
variations are passed as evaluation-time parameters and never change the
engine; the catalogue is evaluation/test data, never real-world data.

All values printed here (with ``pytest -s``) are the measured outcomes that
feed ``docs/ml_evaluation_results.md``.
"""
from decimal import Decimal
import time

import django.test as django_tests
from django.contrib.auth import get_user_model

from apps.apartments.models import Apartment
from apps.recommendations.models import Preference
from ml import evaluation
from ml.evaluation_scenarios import (
    formal_evaluation_catalogue,
    relevance_indices,
)
from ml.features import DEFAULT_FEATURE_WEIGHTS
from ml.ranking import hard_filter_queryset, recommend

User = get_user_model()
PASSWORD = "StrongPass123!"

# Generous single-run bound so a slow/CI runner is not flaky while a genuine
# slowdown still fails (the Sprint 7.6 engine measurement was ~0.015 s).
RESPONSE_TIME_BOUND_SECONDS = 2.0

K_VALUES = (3, 5, 7)


def _create_catalogue_apartments(landlord):
    """Seed real apartments from the formal evaluation catalogue (AGENTS 40)."""
    catalogued = {}
    for index, spec in enumerate(formal_evaluation_catalogue(), start=1):
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
            availability=spec["availability"],
        )
    return catalogued


class FormalWeightedKnnEvaluationTests(django_tests.TestCase):
    """Formal, multi-case measurement of the Weighted KNN component."""

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
        cls.index_by_pk = {apt.pk: index for index, apt in cls.apartments.items()}

    def _preference(self, **overrides):
        params = dict(tenant=self.tenant, location="Calabar", max_rent="300000.00")
        params.update(overrides)
        return Preference.objects.create(**params)

    def _assert_metrics_valid(self, metrics):
        for value in metrics.values():
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 1.0)

    def _run_case(self, case_id, label, preference_overrides, truth_profile,
                  weights=None, k_values=K_VALUES, print_results=True):
        """Run one evaluation case through the real engine at several K values.

        Returns ``{k: {"results": [...], "metrics": {...}}}`` and, when
        ``print_results``, prints the measured metric table (captured with
        ``pytest -s`` for the Chapter Four report).
        """
        preference = self._preference(**preference_overrides)
        relevant_indices = sorted(relevance_indices(
            formal_evaluation_catalogue(), truth_profile))
        relevant_pks = {self.apartments[index].pk for index in relevant_indices}

        eligible_pks = set(
            hard_filter_queryset(Apartment.objects.all(), preference)
            .values_list("pk", flat=True)
        )
        eligible_indices = sorted(self.index_by_pk[pk] for pk in eligible_pks)

        if print_results:
            print(f"\n### [{case_id}] {label}")
            print(f"- relevant (ground-truth indices): {relevant_indices}")
            print(f"- eligible after hard filters (indices): {eligible_indices}")
            print("")
            print("| K | returned | precision | recall | hit_rate | ndcg |")
            print("|---|----------|-----------|--------|----------|------|")

        outcome = {}
        for k in k_values:
            results = recommend(
                Apartment.objects.all(), preference, k=k, weights=weights)
            metrics = evaluation.evaluate(results, relevant_pks, k=k)
            self._assert_metrics_valid(metrics)
            outcome[k] = {"results": results, "metrics": metrics}
            if print_results:
                print(
                    f"| {k} | {len(results)} | {metrics['precision']:.4f} | "
                    f"{metrics['recall']:.4f} | {metrics['hit_rate']:.4f} | "
                    f"{metrics['ndcg']:.4f} |"
                )
        return outcome

    # ------------------------------------------------------------------ #
    # Case matrix (measured values printed for the Chapter Four report)
    # ------------------------------------------------------------------ #

    def test_case_matrix_relevance_metrics(self):
        # Every case is run at K = 3, 5 and 7 with the default (production)
        # weights. Metrics must be bounded; the printed tables record the real
        # measured values.
        cases = [
            ("E1", "Calabar 2-bed under N300k (strict)",
             dict(location="Calabar", max_rent="300000.00",
                  apartment_type=Apartment.ApartmentType.TWO_BEDROOM,
                  bedrooms=2, bathrooms=2),
             dict(location="Calabar", max_rent="300000.00",
                  apartment_type="TWO_BEDROOM", bedrooms=2, bathrooms=2)),
            ("E2", "Calabar relaxed type/size (honest precision)",
             dict(location="Calabar", max_rent="300000.00",
                  apartment_type=None, bedrooms=1, bathrooms=1),
             dict(location="Calabar", max_rent="300000.00",
                  apartment_type="TWO_BEDROOM", bedrooms=2, bathrooms=2)),
            ("E3", "Enugu 2-bed under N320k",
             dict(location="Enugu", max_rent="320000.00",
                  apartment_type=Apartment.ApartmentType.TWO_BEDROOM,
                  bedrooms=2, bathrooms=2),
             dict(location="Enugu", max_rent="320000.00",
                  apartment_type="TWO_BEDROOM", bedrooms=2, bathrooms=2)),
            ("E4", "Enugu relaxed 2-bed under N400k (K/weights experiment)",
             dict(location="Enugu", max_rent="400000.00",
                  apartment_type=None, bedrooms=2, bathrooms=2),
             dict(location="Enugu", max_rent="400000.00",
                  apartment_type="TWO_BEDROOM", bedrooms=2, bathrooms=2)),
            ("E5", "Abuja 3-bed with parking under N700k",
             dict(location="Abuja", max_rent="700000.00",
                  apartment_type=Apartment.ApartmentType.THREE_BEDROOM,
                  bedrooms=3, bathrooms=3, parking=True),
             dict(location="Abuja", max_rent="700000.00",
                  apartment_type="THREE_BEDROOM", bedrooms=3, bathrooms=3,
                  parking=True)),
            ("E6", "Enugu price cap N200k",
             dict(location="Enugu", max_rent="200000.00"),
             dict(location="Enugu", max_rent="200000.00")),
            ("E7", "Abuja DUPLEX type filter",
             dict(location="Abuja", apartment_type=Apartment.ApartmentType.DUPLEX,
                  max_rent="1500000.00"),
             dict(location="Abuja", apartment_type="DUPLEX",
                  max_rent="1500000.00")),
            ("E8", "Enugu 2-bed relaxed (availability check)",
             dict(location="Enugu", max_rent="400000.00",
                  apartment_type=None, bedrooms=2, bathrooms=2),
             dict(location="Enugu", max_rent="400000.00",
                  apartment_type="TWO_BEDROOM", bedrooms=2, bathrooms=2)),
        ]
        for case_id, label, overrides, truth in cases:
            self._run_case(case_id, label, overrides, truth)

    # ------------------------------------------------------------------ #
    # Known-value checks (expected distance/ranking/metrics are documented)
    # ------------------------------------------------------------------ #

    def test_known_value_ranking_and_metrics(self):
        # E1 (strict): exactly 5 eligible apartments, all 5 relevant. Distance
        # is driven only by rental price (type matches, size matches), so the
        # expected ascending-price ranking is [2, 7, 6, 1, 8] and every metric
        # is perfect once K >= 5 (at K=3 recall is 3/5).
        e1 = self._run_case(
            "E1K", "known-value: Calabar 2-bed strict",
            dict(location="Calabar", max_rent="300000.00",
                 apartment_type=Apartment.ApartmentType.TWO_BEDROOM,
                 bedrooms=2, bathrooms=2),
            dict(location="Calabar", max_rent="300000.00",
                 apartment_type="TWO_BEDROOM", bedrooms=2, bathrooms=2),
            print_results=False,
        )
        top5 = [self.index_by_pk[r["apartment"].pk] for r in e1[5]["results"]]
        self.assertEqual(top5, [2, 7, 6, 1, 8])
        distances = [r["distance"] for r in e1[5]["results"]]
        self.assertEqual(distances, sorted(distances))

        m3 = e1[3]["metrics"]
        self.assertEqual(round(m3["precision"], 4), 1.0)
        self.assertEqual(round(m3["recall"], 4), 0.6)
        self.assertEqual(round(m3["hit_rate"], 4), 1.0)
        self.assertEqual(round(m3["ndcg"], 4), 1.0)
        for k in (5, 7):
            m = e1[k]["metrics"]
            self.assertEqual(round(m["precision"], 4), 1.0)
            self.assertEqual(round(m["recall"], 4), 1.0)
            self.assertEqual(round(m["hit_rate"], 4), 1.0)
            self.assertEqual(round(m["ndcg"], 4), 1.0)

        # E4 (relaxed): 7 eligible, 5 ground-truth relevant (the unavailable
        # Enugu 2-bed, index 31, matches the stated preference but is never
        # eligible). With default weights the price dimension dominates and
        # beds/baths fully match the 2-bed candidates, so the expected top-5 is
        # [18, 20, 21, 16, 15] (the N260k/N240k flats outrank the N220k 2-bed
        # because they are price-closer to the N400k query). Measured metrics
        # are asserted for the documented values.
        e4 = self._run_case(
            "E4K", "known-value: Enugu relaxed 2-bed",
            dict(location="Enugu", max_rent="400000.00",
                 apartment_type=None, bedrooms=2, bathrooms=2),
            dict(location="Enugu", max_rent="400000.00",
                 apartment_type="TWO_BEDROOM", bedrooms=2, bathrooms=2),
            print_results=False,
        )
        top5 = [self.index_by_pk[r["apartment"].pk] for r in e4[5]["results"]]
        self.assertEqual(top5, [18, 20, 21, 16, 15])
        distances = [r["distance"] for r in e4[5]["results"]]
        self.assertEqual(distances, sorted(distances))

        m5 = e4[5]["metrics"]
        self.assertAlmostEqual(m5["precision"], 0.6, places=4)
        self.assertAlmostEqual(m5["recall"], 0.6, places=4)
        self.assertEqual(m5["hit_rate"], 1.0)
        self.assertAlmostEqual(m5["ndcg"], 0.616, places=2)

        m7 = e4[7]["metrics"]
        self.assertAlmostEqual(m7["precision"], 4 / 7, places=4)
        self.assertAlmostEqual(m7["recall"], 0.8, places=4)
        self.assertEqual(m7["hit_rate"], 1.0)
        self.assertAlmostEqual(m7["ndcg"], 0.729, places=2)

    # ------------------------------------------------------------------ #
    # K behaviour
    # ------------------------------------------------------------------ #

    def test_k_behaviour_prefix_property(self):
        # E4 has exactly 7 eligible candidates so every K is genuinely binding
        # and K=3/5 are strict prefixes of K=7 in the same relative order.
        preference = self._preference(
            location="Enugu", max_rent="400000.00",
            apartment_type=None, bedrooms=2, bathrooms=2)
        r3 = recommend(Apartment.objects.all(), preference, k=3)
        r5 = recommend(Apartment.objects.all(), preference, k=5)
        r7 = recommend(Apartment.objects.all(), preference, k=7)
        self.assertEqual(len(r3), 3)
        self.assertEqual(len(r5), 5)
        self.assertEqual(len(r7), 7)
        pks = lambda results: [r["apartment"].pk for r in results]
        self.assertEqual(pks(r3), pks(r5)[:3])
        self.assertEqual(pks(r3), pks(r7)[:3])
        self.assertEqual(pks(r5), pks(r7)[:5])

        # E1 has only 5 eligible candidates: K=7 degrades gracefully to all 5.
        strict = self._preference(
            max_rent="300000.00",
            apartment_type=Apartment.ApartmentType.TWO_BEDROOM,
            bedrooms=2, bathrooms=2)
        full = recommend(Apartment.objects.all(), strict, k=7)
        self.assertEqual(len(full), 5)
        small = recommend(Apartment.objects.all(), strict, k=3)
        self.assertEqual(pks(small), pks(full)[:3])

    # ------------------------------------------------------------------ #
    # Hard-filter verification (AGENTS 15)
    # ------------------------------------------------------------------ #

    def test_hard_filters_are_respected_in_every_case(self):
        cases = [
            dict(location="Calabar", max_rent="300000.00",
                 apartment_type=Apartment.ApartmentType.TWO_BEDROOM,
                 bedrooms=2, bathrooms=2),
            dict(location="Calabar", max_rent="300000.00",
                 apartment_type=None, bedrooms=1, bathrooms=1),
            dict(location="Enugu", max_rent="320000.00",
                 apartment_type=Apartment.ApartmentType.TWO_BEDROOM,
                 bedrooms=2, bathrooms=2),
            dict(location="Enugu", max_rent="400000.00",
                 apartment_type=None, bedrooms=2, bathrooms=2),
            dict(location="Abuja", max_rent="700000.00",
                 apartment_type=Apartment.ApartmentType.THREE_BEDROOM,
                 bedrooms=3, bathrooms=3, parking=True),
            dict(location="Enugu", max_rent="200000.00"),
            dict(location="Abuja", apartment_type=Apartment.ApartmentType.DUPLEX,
                 max_rent="1500000.00"),
        ]
        for overrides in cases:
            preference = self._preference(**overrides)
            results = recommend(Apartment.objects.all(), preference, k=7)
            self.assertGreaterEqual(len(results), 1)
            for result in results:
                apartment = result["apartment"]
                self.assertTrue(apartment.availability)
                if preference.location:
                    self.assertIn(preference.location.lower(),
                                  apartment.location.lower())
                if preference.max_rent is not None:
                    self.assertLessEqual(Decimal(apartment.rental_price),
                                         Decimal(preference.max_rent))
                if preference.apartment_type:
                    self.assertEqual(apartment.apartment_type,
                                     preference.apartment_type)
                if preference.bedrooms is not None:
                    self.assertGreaterEqual(apartment.bedrooms,
                                            preference.bedrooms)
                if preference.bathrooms is not None:
                    self.assertGreaterEqual(apartment.bathrooms,
                                            preference.bathrooms)
                for field in ("parking", "electricity", "water", "security",
                              "furnished"):
                    if getattr(preference, field) is True:
                        self.assertTrue(getattr(apartment, field))

    def test_unavailable_apartment_is_never_recommended(self):
        # The Enugu 2-bed N250k candidate (index 31) satisfies every stated
        # preference filter except availability; it must never be eligible or
        # appear in any ranking (AGENTS 15).
        preference = self._preference(
            location="Enugu", max_rent="400000.00",
            apartment_type=None, bedrooms=2, bathrooms=2)
        eligible_pks = set(
            hard_filter_queryset(Apartment.objects.all(), preference)
            .values_list("pk", flat=True))
        self.assertNotIn(self.apartments[31].pk, eligible_pks)
        results = recommend(Apartment.objects.all(), preference, k=7)
        self.assertNotIn(self.apartments[31].pk,
                         {r["apartment"].pk for r in results})

    # ------------------------------------------------------------------ #
    # Weight-configuration comparison (evaluation-time overrides only)
    # ------------------------------------------------------------------ #

    def test_weight_configuration_comparison(self):
        # Compare default (production), uniform (experimental) and a
        # facility-focused (experimental) configuration on the two relaxed
        # cases. Weights are passed to the real engine as evaluation-time
        # parameters; the engine and its defaults are unchanged.
        uniform = {feature: 1.0 for feature in DEFAULT_FEATURE_WEIGHTS}
        facility_focused = dict(DEFAULT_FEATURE_WEIGHTS)
        for feature in ("parking", "electricity", "water", "security",
                        "furnished"):
            facility_focused[feature] = 3.0

        configs = [
            ("default (production)", None),
            ("uniform (experimental)", uniform),
            ("facility-focused (experimental)", facility_focused),
        ]
        cases = [
            ("E2", "Calabar relaxed",
             dict(location="Calabar", max_rent="300000.00",
                  apartment_type=None, bedrooms=1, bathrooms=1),
             dict(location="Calabar", max_rent="300000.00",
                  apartment_type="TWO_BEDROOM", bedrooms=2, bathrooms=2)),
            ("E4", "Enugu relaxed",
             dict(location="Enugu", max_rent="400000.00",
                  apartment_type=None, bedrooms=2, bathrooms=2),
             dict(location="Enugu", max_rent="400000.00",
                  apartment_type="TWO_BEDROOM", bedrooms=2, bathrooms=2)),
        ]

        print("\n### Weight configuration comparison (K = 5)")
        print("| Case | config | precision | recall | hit_rate | ndcg | top-1 |")
        print("|------|--------|-----------|--------|----------|------|-------|")
        for case_id, label, overrides, truth in cases:
            preference = self._preference(**overrides)
            relevant_pks = {
                self.apartments[index].pk
                for index in relevance_indices(formal_evaluation_catalogue(),
                                               truth)
            }
            for config_label, weights in configs:
                results = recommend(Apartment.objects.all(), preference, k=5,
                                    weights=weights)
                self.assertEqual(len(results), 5)
                metrics = evaluation.evaluate(results, relevant_pks, k=5)
                self._assert_metrics_valid(metrics)
                top1 = self.index_by_pk[results[0]["apartment"].pk]
                print(
                    f"| {case_id} | {config_label} | {metrics['precision']:.4f} "
                    f"| {metrics['recall']:.4f} | {metrics['hit_rate']:.4f} | "
                    f"{metrics['ndcg']:.4f} | {top1} |"
                )

    # ------------------------------------------------------------------ #
    # Output consistency and reproducibility
    # ------------------------------------------------------------------ #

    def test_output_consistency_across_repeated_runs(self):
        preference = self._preference(
            location="Enugu", max_rent="400000.00",
            apartment_type=None, bedrooms=2, bathrooms=2)
        first = recommend(Apartment.objects.all(), preference, k=7)
        second = recommend(Apartment.objects.all(), preference, k=7)
        for a, b in zip(first, second):
            self.assertEqual(a["apartment"].pk, b["apartment"].pk)
            self.assertEqual(a["distance"], b["distance"])
            self.assertEqual(a["rank"], b["rank"])

    # ------------------------------------------------------------------ #
    # Response time (measured, never fabricated - AGENTS 28, 40)
    # ------------------------------------------------------------------ #

    def test_formal_evaluation_response_time(self):
        # Time the whole pipeline over the full 32-candidate catalogue with no
        # restricting filters, so every available apartment is ranked.
        preference = self._preference(location="", max_rent=None)
        eligible = hard_filter_queryset(
            Apartment.objects.all(), preference).count()
        start = time.perf_counter()
        results = recommend(Apartment.objects.all(), preference, k=7)
        elapsed = time.perf_counter() - start

        # 30 available apartments; only K=7 are returned by the engine.
        self.assertEqual(eligible, 30)
        self.assertEqual(len(results), 7)
        self.assertLess(elapsed, RESPONSE_TIME_BOUND_SECONDS)
        print(f"\nMeasured Weighted KNN response time over the 32-candidate "
              f"catalogue (30 available) = {elapsed:.4f}s")