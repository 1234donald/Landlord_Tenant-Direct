"""
User-acceptance and usability evaluation tests for Phase 7, Sprint 7.5.

Sprint 7.5 (SYSTEM_REQUIREMENTS §41, §29.3) evaluates: registration,
navigation, apartment search, apartment information, the recommendation
interface, messaging and overall usability.

Unlike a typical human survey, this automated suite measures the *running
system* directly so every assertion is a real, observable outcome (AGENTS 28,
39, 40: only actual results, never fabricated participant feedback). It is
paired with a human-administered acceptance checklist (see README) that a
reviewer fills in by actually using the application.

Each evaluation target is mapped to measurable live-system checks:

- Registration        -> REST registration returns a clear, consistent success
   and a human-readable error message when input is invalid.
- Navigation          -> role-based navbar entries are shown to the right role
   and every internal link on the public pages resolves (no broken links).
- Apartment search    -> the browse page renders the full sentence of search
   filters and a filtered search returns the correct, clearly labelled result.
- Apartment info      -> the detail page presents every listing field (§10):
   title, price, location, type, bedrooms, bathrooms, facilities, description.
- Recommendation UI   -> the results page explains Weighted KNN, shows ranked
   cards with rank + similarity score, and uses factual terminology (AGENTS 43).
- Messaging           -> the messaging API gives clear success/error feedback
   and supports a tenant sending a message to a landlord.
- Overall usability   -> every page shares one base layout (consistent header,
   navigation and footer), carries a responsive viewport, and renders a single
   <main> landmark and an accessible navigation (AGENTS 42, §29.3).
"""
import re

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.apartments.models import Apartment

User = get_user_model()

LOGIN_URL = "/api/v1/auth/login/"
REGISTER_URL = "/api/v1/auth/register/"
CONVERSATIONS_URL = "/api/v1/conversations/"
PASSWORD = "StrongPass123!"

PUBLIC_PAGES = [
    "/",
    "/about/",
    "/apartments/",
]


def create_landlord(email="landlord@example.com", full_name="Landlord User"):
    return User.objects.create_user(
        email=email,
        password=PASSWORD,
        full_name=full_name,
        role=User.Role.LANDLORD,
    )


def create_tenant(email="tenant@example.com", full_name="Tenant User"):
    return User.objects.create_user(
        email=email,
        password=PASSWORD,
        full_name=full_name,
        role=User.Role.TENANT,
    )


def create_apartment(landlord, **overrides):
    payload = {
        "title": "Sunny Two-Bedroom Flat",
        "description": "A bright, well-maintained flat in the city centre.",
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
        "additional_facilities": "24-hour security, borehole water",
        "availability": True,
    }
    payload.update(overrides)
    return Apartment.objects.create(landlord=landlord, **payload)


def _internal_links(html):
    """Return internal page hrefs parsed from an HTML document.

    Static asset urls (``/static/...``) are excluded: they are not navigable
    pages and are served by Nginx at deployment (AGENTS 44), not by the Django
    routes exercised here.
    """
    hrefs = re.findall(r'href="(/[^"]*)"', html)
    return [h for h in hrefs if h not in ("#", "/#") and not h.startswith("/static/")]


class RegistrationUsabilityTests(TestCase):
    """Registration presents clear, consistent user feedback."""

    def test_successful_registration_gives_clear_feedback(self):
        response = self.client.post(
            REGISTER_URL,
            {
                "email": "newtenant@example.com",
                "password": PASSWORD,
                "full_name": "New Tenant",
                "role": User.Role.TENANT,
            },
            format="json",
            HTTP_HOST="localhost",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["message"], "Registration successful.")

    def test_invalid_registration_gives_understandable_error(self):
        # Missing required fields -> a human-readable "Registration failed."
        # message plus per-field errors the user can act on.
        response = self.client.post(
            REGISTER_URL,
            {"email": "broken-email"},
            format="json",
            HTTP_HOST="localhost",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertFalse(body["success"])
        self.assertEqual(body["message"], "Registration failed.")
        self.assertIn("errors", body)
        self.assertIn("password", body["errors"])


class NavigationUsabilityTests(TestCase):
    """Navigation is consistent, role-appropriate and free of broken links."""

    def test_public_pages_have_no_broken_internal_links(self):
        # Crawl the public pages; every internal link must resolve 200.
        for path in PUBLIC_PAGES:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                for link in _internal_links(response.content.decode()):
                    with self.subTest(link=link):
                        target = self.client.get(link)
                        self.assertNotEqual(
                            target.status_code, status.HTTP_404_NOT_FOUND
                        )
                        self.assertNotEqual(
                            target.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
                        )

    def test_apartment_detail_page_links_resolve(self):
        landlord = create_landlord()
        apartment = create_apartment(landlord)
        detail = self.client.get(f"/apartments/{apartment.pk}/")
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        for link in _internal_links(detail.content.decode()):
            target = self.client.get(link)
            self.assertNotEqual(
                target.status_code, status.HTTP_404_NOT_FOUND
            )

    def test_landlord_sees_my_apartments_in_navigation(self):
        landlord = create_landlord()
        self.client.force_login(landlord)
        home = self.client.get("/")
        self.assertContains(home, "My Apartments")
        self.assertNotContains(home, "Recommendations")
        self.assertNotContains(home, "Admin")

    def test_tenant_sees_recommendations_in_navigation(self):
        tenant = create_tenant()
        self.client.force_login(tenant)
        home = self.client.get("/")
        self.assertContains(home, "Recommendations")
        self.assertNotContains(home, "My Apartments")
        self.assertNotContains(home, "Admin")

    def test_admin_sees_admin_dashboard_in_navigation(self):
        admin = User.objects.create_user(
            email="admin@example.com",
            password=PASSWORD,
            full_name="Admin User",
            role=User.Role.ADMIN,
        )
        self.client.force_login(admin)
        home = self.client.get("/")
        self.assertContains(home, "Admin")
        for label in ("Dashboard", "Users", "Landlords", "Apartments", "Verifications"):
            self.assertContains(home, label)


class ApartmentSearchUsabilityTests(TestCase):
    """The search interface exposes the full set of filters and returns clear
    results."""

    def test_browse_page_renders_all_search_filters(self):
        response = self.client.get("/apartments/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        html = response.content.decode()
        for field in ("location", "apartment_type", "min_price", "max_price",
                      "bedrooms", "bathrooms", "parking", "electricity",
                      "water", "security", "furnished"):
            self.assertIn(f'name="{field}"', html)

    def test_filtered_search_returns_matching_clearly_displayed_result(self):
        landlord = create_landlord()
        create_apartment(landlord, title="Calabar Flat", location="Calabar")
        create_apartment(
            landlord,
            title="Uyo Flat",
            location="Uyo",
            rental_price="120000.00",
            apartment_type=Apartment.ApartmentType.ONE_BEDROOM,
            bedrooms=1,
            bathrooms=1,
        )
        response = self.client.get("/apartments/", {"location": "Calabar"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Calabar Flat")
        self.assertNotContains(response, "Uyo Flat")


class ApartmentInformationUsabilityTests(TestCase):
    """The detail page presents every listing field clearly (§10)."""

    def test_detail_page_shows_all_key_information(self):
        landlord = create_landlord(full_name="Mr Landlord")
        apartment = create_apartment(
            landlord,
            title="Sunny Two-Bedroom Flat",
            location="Calabar",
            rental_price="250000.00",
        )
        detail = self.client.get(f"/apartments/{apartment.pk}/")
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        for fragment in (
            "Sunny Two-Bedroom Flat",  # title
            "250000",  # rental price (floatformat:0)
            "Calabar",  # location
            "Bedrooms",  # bedroom section label
            "Bathrooms",  # bathroom section label
            "Parking",  # facilities
            "Electricity",
            "Water",
            "Security",
            "Two-bedroom",  # type display
            "Mr Landlord",  # landlord name
            "landlord@example.com",  # landlord email
        ):
            self.assertContains(detail, fragment)


class RecommendationInterfaceUsabilityTests(TestCase):
    """The recommendation page is reachable, explains the approach and shows
    ranked results with factual terminology (AGENTS 43)."""

    def test_recommendation_page_reachable_and_explains_approach(self):
        tenant = create_tenant()
        self.client.force_login(tenant)
        page = self.client.get(reverse("recommendation-results"))
        self.assertEqual(page.status_code, status.HTTP_200_OK)
        self.assertContains(page, "Recommended for you")
        self.assertContains(page, "Weighted KNN")

    def test_recommendation_page_uses_factual_terminology(self):
        tenant = create_tenant()
        landlord = create_landlord()
        create_apartment(landlord, title="Recommended Flat")
        from apps.recommendations.models import Preference, Recommendation

        Preference.objects.create(
            tenant=tenant,
            location="Calabar",
            max_rent="300000.00",
            apartment_type=Apartment.ApartmentType.TWO_BEDROOM,
            bedrooms=2,
            bathrooms=2,
        )
        self.client.force_login(tenant)
        self.client.post(reverse("recommendation-results"))
        page = self.client.get(reverse("recommendation-results"))
        self.assertContains(page, "Rank 1")
        self.assertContains(page, "Similarity score")
        # Factual, non-guarantee language only (AGENTS 43).
        self.assertNotContains(page, "Guaranteed best")
        self.assertNotContains(page, "guaranteed")


class MessagingUsabilityTests(TestCase):
    """Messaging gives clear feedback and supports tenant-to-landlord contact."""

    def _login(self, user):
        response = self.client.post(
            LOGIN_URL,
            {"email": user.email, "password": PASSWORD},
            format="json",
            HTTP_HOST="localhost",
        )
        access = response.json()["data"]["access"]
        self.client = APIClient(HTTP_HOST="localhost")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def test_tenant_can_start_conversation_with_landlord(self):
        landlord = create_landlord()
        tenant = create_tenant()
        self._login(tenant)
        response = self.client.post(
            CONVERSATIONS_URL,
            {"counterpart": landlord.pk},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertIn("Conversation", body["message"])

    def test_messaging_gives_clear_error_for_missing_counterpart(self):
        tenant = create_tenant()
        self._login(tenant)
        response = self.client.post(
            CONVERSATIONS_URL,
            {},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertFalse(body["success"])
        self.assertIn("Conversation creation failed", body["message"])
        self.assertIn("counterpart", body["errors"])


class OverallUsabilityTests(TestCase):
    """Pages are consistent, responsive and accessible (AGENTS 42, §29.3)."""

    def test_all_pages_share_consistent_layout_and_responsive_viewport(self):
        landlord = create_landlord()
        apartment = create_apartment(landlord)
        tenant = create_tenant()
        self.client.force_login(tenant)
        pages = [
            "/",
            "/about/",
            "/apartments/",
            f"/apartments/{apartment.pk}/",
            reverse("recommendation-results"),
        ]
        for url in pages:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                html = response.content.decode()
                # Consistent shared base: navbar, footer and responsive viewport.
                self.assertIn('<meta name="viewport"', html)
                self.assertIn('class="navbar', html)
                self.assertIn('class="footer"', html)
                # Accessibility basics: a main landmark and a nav landmark.
                self.assertIn("<main", html)
                self.assertIn("<nav", html)
                # A single page heading for orientation.
                self.assertIn("<h1", html)

    def test_apartment_page_has_structured_headings(self):
        landlord = create_landlord()
        apartment = create_apartment(landlord)
        detail = self.client.get(f"/apartments/{apartment.pk}/")
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        html = detail.content.decode()
        self.assertIn("<h1", html)
        # Structured content sections use heading levels (Overhead Overview/Facilities).
        self.assertIn("<h2", html)
        self.assertIn("<h3", html)
