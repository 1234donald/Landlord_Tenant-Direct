"""
Unit tests for Phase 5, Sprint 5.5 - KNN candidate selection and ranking.

These verify the Weighted KNN ranking engine deliverable in ``ml.ranking``:
applying the Sprint 5.1 hard filters before ranking, calculating distances,
sorting ascending, selecting K nearest, assigning ranking positions, and
handling limited-candidate (fewer than K) cases.
"""
import django.test as django_tests
from django.contrib.auth import get_user_model

from apps.apartments.models import Apartment
from apps.recommendations.models import Preference
from ml.features import DEFAULT_K
from ml.ranking import hard_filter_queryset, rank_recommendations, recommend

User = get_user_model()
PASSWORD = "StrongPass123!"


def make_landlord():
    return User.objects.create_user(
        email="landlord@example.com",
        password=PASSWORD,
        full_name="Landlord",
        role=User.Role.LANDLORD,
    )


def make_apartment(landlord, **overrides):
    defaults = {
        "title": "Flat",
        "location": "Calabar",
        "rental_price": "250000.00",
        "apartment_type": Apartment.ApartmentType.TWO_BEDROOM,
        "bedrooms": 2,
        "bathrooms": 2,
        "parking": True,
        "electricity": True,
        "water": True,
        "security": True,
        "furnished": False,
        "availability": True,
    }
    defaults.update(overrides)
    return Apartment.objects.create(landlord=landlord, **defaults)


class HardFilterTests(django_tests.TestCase):
    def setUp(self):
        self.landlord = make_landlord()
        self.base = Apartment.objects.all()

    def _preference(self, **kwargs):
        tenant = User.objects.create_user(
            email="tenant@example.com", password=PASSWORD,
            full_name="Tenant", role=User.Role.TENANT,
        )
        return Preference.objects.create(tenant=tenant, **kwargs)

    def test_price_cap_excludes_over_budget(self):
        make_apartment(self.landlord, title="In budget", rental_price="400000.00")
        make_apartment(self.landlord, title="Over budget", rental_price="600000.00")
        preference = self._preference(max_rent="500000.00")
        eligible = hard_filter_queryset(self.base, preference)
        titles = {a.title for a in eligible}
        self.assertEqual(titles, {"In budget"})

    def test_availability_required(self):
        make_apartment(self.landlord, title="Available")
        make_apartment(self.landlord, title="Unavailable", availability=False)
        preference = self._preference()
        titles = {a.title for a in hard_filter_queryset(self.base, preference)}
        self.assertEqual(titles, {"Available"})

    def test_location_match(self):
        make_apartment(self.landlord, title="Calabar flat", location="Calabar")
        make_apartment(self.landlord, title="Uyo flat", location="Uyo")
        preference = self._preference(location="calabar")
        titles = {a.title for a in hard_filter_queryset(self.base, preference)}
        self.assertEqual(titles, {"Calabar flat"})

    def test_apartment_type_exact_match(self):
        make_apartment(
            self.landlord, title="Two bed",
            apartment_type=Apartment.ApartmentType.TWO_BEDROOM,
        )
        make_apartment(
            self.landlord, title="Duplex",
            apartment_type=Apartment.ApartmentType.DUPLEX,
        )
        preference = self._preference(apartment_type=Apartment.ApartmentType.TWO_BEDROOM)
        titles = {a.title for a in hard_filter_queryset(self.base, preference)}
        self.assertEqual(titles, {"Two bed"})

    def test_required_facility_filters(self):
        make_apartment(self.landlord, title="Has parking", parking=True)
        make_apartment(self.landlord, title="No parking", parking=False)
        preference = self._preference(parking=True)
        titles = {a.title for a in hard_filter_queryset(self.base, preference)}
        self.assertEqual(titles, {"Has parking"})

    def test_optional_facility_rejected_does_not_filter(self):
        make_apartment(self.landlord, title="Unfurnished", furnished=False)
        make_apartment(self.landlord, title="Furnished", furnished=True)
        preference = self._preference(furnished=False)
        self.assertEqual(hard_filter_queryset(self.base, preference).count(), 2)

    def test_unit_minimums(self):
        make_apartment(self.landlord, title="2 bed", bedrooms=2, bathrooms=2)
        make_apartment(self.landlord, title="1 bed", bedrooms=1, bathrooms=1)
        preference = self._preference(bedrooms=2, bathrooms=2)
        titles = {a.title for a in hard_filter_queryset(self.base, preference)}
        self.assertEqual(titles, {"2 bed"})


class RankingTests(django_tests.TestCase):
    def setUp(self):
        self.landlord = make_landlord()
        self.base = Apartment.objects.all()
        self.tenant = User.objects.create_user(
            email="tenant@example.com", password=PASSWORD,
            full_name="Tenant", role=User.Role.TENANT,
        )

    def _preference(self, **kwargs):
        defaults = {
            "max_rent": "300000.00",
            "apartment_type": Apartment.ApartmentType.TWO_BEDROOM,
            "bedrooms": 2,
            "bathrooms": 2,
        }
        defaults.update(kwargs)
        return Preference.objects.create(tenant=self.tenant, **defaults)

    def test_ranks_by_ascending_distance(self):
        # Query target price = max_rent = 300000; cheapest is furthest.
        cheap = make_apartment(self.landlord, title="Cheap", rental_price="200000.00")
        near = make_apartment(self.landlord, title="Near budget", rental_price="300000.00")
        mid = make_apartment(self.landlord, title="Mid", rental_price="250000.00")

        results = hard_filter_queryset(self.base, self._preference())
        ranked = rank_recommendations(results, self._preference())
        titles = [r["apartment"].title for r in ranked]
        self.assertEqual(titles, ["Near budget", "Mid", "Cheap"])

    def test_ranks_are_1_based_contiguous(self):
        make_apartment(self.landlord, rental_price="200000.00")
        make_apartment(self.landlord, rental_price="300000.00")
        make_apartment(self.landlord, rental_price="250000.00")
        ranked = recommend(self.base, self._preference())
        self.assertEqual([r["rank"] for r in ranked], [1, 2, 3])
        for r in ranked:
            self.assertGreaterEqual(r["similarity"], 0.0)
            self.assertLessEqual(r["similarity"], 1.0)

    def test_selects_k_nearest(self):
        for price in ("100000", "150000", "200000", "250000", "300000"):
            make_apartment(self.landlord, rental_price=price)
        ranked = recommend(self.base, self._preference(), k=3)
        self.assertEqual(len(ranked), 3)
        self.assertEqual([r["rank"] for r in ranked], [1, 2, 3])

    def test_default_k_is_configurable_constant(self):
        self.assertIsInstance(DEFAULT_K, int)
        self.assertGreater(DEFAULT_K, 0)

    def test_limited_candidates_return_all(self):
        make_apartment(self.landlord, rental_price="200000.00")
        make_apartment(self.landlord, rental_price="300000.00")
        ranked = recommend(self.base, self._preference(), k=5)
        self.assertEqual(len(ranked), 2)
        self.assertEqual([r["rank"] for r in ranked], [1, 2])

    def test_empty_candidates_return_empty(self):
        make_apartment(self.landlord, rental_price="900000.00")
        # Preference caps at 500000 -> nothing eligible.
        preference = self._preference(max_rent="500000.00")
        self.assertEqual(recommend(self.base, preference), [])

    def test_recommend_applies_hard_filters_then_ranks(self):
        # A similar but over-budget apartment is excluded by the price cap.
        make_apartment(self.landlord, title="Eligible", rental_price="280000.00")
        make_apartment(self.landlord, title="Too expensive", rental_price="800000.00")
        results = recommend(self.base, self._preference(max_rent="300000.00"))
        self.assertEqual([r["apartment"].title for r in results], ["Eligible"])

    def test_distance_is_finite(self):
        import math

        make_apartment(self.landlord, rental_price="250000.00")
        for result in recommend(self.base, self._preference()):
            self.assertTrue(math.isfinite(result["distance"]))
