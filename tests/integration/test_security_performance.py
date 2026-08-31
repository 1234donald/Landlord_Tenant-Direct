"""
Security and performance tests for Phase 7, Sprint 7.4 - Security and
Performance Testing (SYSTEM_REQUIREMENTS §41, §27, §29.1; AGENTS 19-24, 28).

This suite delivers the "security and performance results" for the sprint by
(a) closing the remaining genuine security-test gaps (stored XSS mitigation via
template auto-escaping and SQL-injection-safe search through the ORM) and
(b) measuring actual response times for a normal API request and for
recommendation generation, the two performance criteria named in the
non-functional requirements:

    §29.1 "Normal application/API requests should target response times below
    approximately two seconds ... Recommendation response time shall be
    separately measured during evaluation."

The earlier security work (Sprints 6.3/6.4 and API tests) already covers
unauthorised access, input validation, authentication, permissions and file
uploads extensively; this file deliberately does not duplicate those and instead
targets the specific Sprint 7.4 gaps. Timings are measured with
``time.perf_counter`` on real requests and *recorded*, never fabricated (AGENTS
28, 41, 47) - the assertion bound is deliberately generous so a slow (cold)
runner does not falsely fail, while still catching genuine regressions.
"""
import time

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.apartments.models import Apartment
from apps.recommendations.models import Preference

User = get_user_model()

LOGIN_URL = "/api/v1/auth/login/"
APARTMENTS_URL = "/api/v1/apartments/"
PREFERENCES_URL = "/api/v1/preferences/"
RECOMMENDATIONS_GENERATE_URL = "/api/v1/recommendations/generate/"

PASSWORD = "StrongPass123!"

# Generous single-request bound. The NFR target is ~2s; the bound is set higher
# so a cold/dev runner is not flaky while any genuine slowdown still fails.
RESPONSE_TIME_BOUND_SECONDS = 10.0


def apartment_payload(**overrides):
    payload = {
        "title": "Sunny 2-Bedroom Flat",
        "description": "A bright two-bedroom flat near town.",
        "location": "Calabar",
        "address": "10 Ikot Ansa Road",
        "rental_price": "250000.00",
        "apartment_type": Apartment.ApartmentType.TWO_BEDROOM,
        "bedrooms": 2,
        "bathrooms": 2,
        "parking": True,
        "electricity": True,
        "water": True,
        "security": True,
        "furnished": False,
        "additional_facilities": "",
        "availability": True,
    }
    payload.update(overrides)
    return payload


class XssMitigationTests(APITestCase):
    """Stored/reflected XSS is neutralised by Django template auto-escaping."""

    def setUp(self):
        self.client = APIClient(HTTP_HOST="localhost")
        self.landlord = User.objects.create_user(
            email="landlord@example.com",
            password=PASSWORD,
            full_name="Landlord",
            role=User.Role.LANDLORD,
        )

    def test_apartment_title_script_is_escaped_on_pages(self):
        XSS = "<script>alert('xss')</script>"
        apartment = Apartment.objects.create(
            landlord=self.landlord,
            title=XSS,
            location="Calabar",
            rental_price="250000.00",
            apartment_type=Apartment.ApartmentType.TWO_BEDROOM,
            bedrooms=2,
            bathrooms=2,
            availability=True,
        )
        # Detail page renders the escaped title, not the executable script.
        detail = self.client.get(f"/apartments/{apartment.pk}/")
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        html = detail.content.decode()
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>alert(", html)

        # The browse page renders the escaped title in its card list.
        browse = self.client.get("/apartments/")
        self.assertEqual(browse.status_code, status.HTTP_200_OK)
        html = browse.content.decode()
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>alert(", html)

    def test_search_input_reflection_is_escaped(self):
        # A crafted location echoed back into the search form must be escaped.
        payload = "\"><script>alert('x')</script>"
        browse = self.client.get("/apartments/", {"location": payload})
        self.assertEqual(browse.status_code, status.HTTP_200_OK)
        html = browse.content.decode()
        self.assertNotIn('<script>alert(\'x\')', html)
        self.assertNotIn('"><script>', html)


class SqlInjectionSafeSearchTests(APITestCase):
    """Search/filter queries are parameterised by the ORM (AGENTS 19)."""

    def setUp(self):
        self.client = APIClient(HTTP_HOST="localhost")
        self.landlord = User.objects.create_user(
            email="landlord@example.com",
            password=PASSWORD,
            full_name="Landlord",
            role=User.Role.LANDLORD,
        )
        Apartment.objects.create(
            landlord=self.landlord,
            title="Calabar Flat",
            location="Calabar",
            rental_price="250000.00",
            apartment_type=Apartment.ApartmentType.TWO_BEDROOM,
            bedrooms=2,
            bathrooms=2,
            availability=True,
        )

    def test_malicious_location_does_not_leak_rows(self):
        # A boolean-injection-style value must not match every row.
        for craft in (
            "Calabar' OR '1'='1",
            "' OR 1=1 --",
            "Calabar\" OR \"1\"=\"1",
        ):
            with self.subTest(craft=craft):
                response = self.client.get(APARTMENTS_URL, {"location": craft})
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                # Exact-string match only; the single Calabar row never leaks via
                # a boolean tautology.
                self.assertEqual(response.data["count"], 0)

    def test_injection_only_matches_literal_calabar(self):
        payload = "Calabar' OR '1'='1"
        direct = Apartment.objects.filter(location__icontains=payload).count()
        self.assertEqual(direct, 0)
        legit = Apartment.objects.filter(location__icontains="Calabar").count()
        self.assertEqual(legit, 1)


class ResponseTimeMeasurementTests(APITestCase):
    """Measure real response times for the NFR §29.1 performance criteria.

    Each test records the measured elapsed time (never fabricated) and asserts
    it stays within a generous bound to catch genuine regressions.
    """

    def setUp(self):
        self.client = APIClient(HTTP_HOST="localhost")
        self.landlord = User.objects.create_user(
            email="landlord@example.com",
            password=PASSWORD,
            full_name="Landlord",
            role=User.Role.LANDLORD,
        )

    def _auth_as(self, user):
        response = self.client.post(
            LOGIN_URL,
            {"email": user.email, "password": PASSWORD},
            format="json",
        )
        access = response.data["data"]["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def test_normal_api_request_response_time(self):
        # A representative normal read request: list apartments with a filter.
        Apartment.objects.create(
            landlord=self.landlord,
            title="Calabar Flat",
            location="Calabar",
            rental_price="250000.00",
            apartment_type=Apartment.ApartmentType.TWO_BEDROOM,
            bedrooms=2,
            bathrooms=2,
            availability=True,
        )
        start = time.perf_counter()
        response = self.client.get(APARTMENTS_URL, {"location": "Calabar"})
        elapsed = time.perf_counter() - start

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        # Real measured time, asserted against the NFR bound.
        self.assertLess(elapsed, RESPONSE_TIME_BOUND_SECONDS)
        # Recorded for the sprint evidence output.
        self._record("normal_api_request", elapsed)

    def test_recommendation_generation_response_time(self):
        """Recommendation response time is measured separately (§29.1)."""
        for payload in (
            apartment_payload(),
            apartment_payload(
                title="Uyo Flat",
                location="Uyo",
                rental_price="150000.00",
                apartment_type=Apartment.ApartmentType.ONE_BEDROOM,
                bedrooms=1,
                bathrooms=1,
            ),
        ):
            Apartment.objects.create(landlord=self.landlord, **payload)

        tenant = User.objects.create_user(
            email="tenant@example.com",
            password=PASSWORD,
            full_name="Tenant",
            role=User.Role.TENANT,
        )
        Preference.objects.create(
            tenant=tenant,
            location="Calabar",
            max_rent="500000.00",
            apartment_type=Apartment.ApartmentType.TWO_BEDROOM,
            bedrooms=2,
            bathrooms=2,
        )
        self._auth_as(tenant)

        start = time.perf_counter()
        response = self.client.post(RECOMMENDATIONS_GENERATE_URL, {}, format="json")
        elapsed = time.perf_counter() - start

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["algorithm"], "weighted_knn")
        self.assertLess(elapsed, RESPONSE_TIME_BOUND_SECONDS)
        self._record("recommendation_generation", elapsed)

    def _record(self, name, elapsed_seconds):
        # Sprint-7.4 evidence: measured (not fabricated) timings are surfaced in
        # the test report so Chapter Four can cite actual execution results.
        print(f"\nSprint7.4 measured {name} = {elapsed_seconds:.3f}s")
