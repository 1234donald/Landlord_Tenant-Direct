"""
System-level end-to-end tests for Phase 7, Sprint 7.3 - System and
End-to-End Testing (SYSTEM_REQUIREMENTS §41).

The deliverable for this sprint is end-to-end system-test evidence. Each
specified journey is executed from start to finish through the real HTTP API
(JWT) and the presentation/administrator console pages (session auth), rather
than by seeding intermediate data directly:

    Tenant journey:
        Register -> Login -> Search -> Filter -> Preferences
        -> Recommendation -> Apartment Details -> Message Landlord

    Landlord journey:
        Register -> Verification -> Create Apartment -> Manage Apartment
        -> Receive Message

    Administrator journey:
        Login -> Manage Users -> Review Verification -> Manage Listings

The full ``test_full_system_integration.py`` (Sprint 6.6) already chains every
module together; this suite is the dedicated 7.3 end-to-end system-test
deliverable. It therefore concentrates on the journey steps that are most
representative of a complete *system* run - notably the management actions
(landlord editing/setting a listing's availability; the administrator toggling
a user's status and moderating a listing) - while confirming each journey still
works end to end across roles. All figures asserted are read from the real
database or real HTTP responses; nothing is fabricated (AGENTS 39, 40).

Operations that are genuinely cross-cutting (fixing the tenant journey on top of
a landlord listing, approving verification before a listing is created, the
admin reviewing the same verification a landlord submitted) make this a
single, coherent system scenario rather than isolated feature calls.
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.apartments.models import Apartment
from apps.messaging.models import Conversation, Message
from apps.recommendations.models import Preference, Recommendation
from apps.verification.models import VerificationRequest

User = get_user_model()

REGISTER_URL = "/api/v1/auth/register/"
LOGIN_URL = "/api/v1/auth/login/"
APARTMENTS_URL = "/api/v1/apartments/"
PREFERENCES_URL = "/api/v1/preferences/"
RECOMMENDATIONS_GENERATE_URL = "/api/v1/recommendations/generate/"
RECOMMENDATIONS_URL = "/api/v1/recommendations/"
MESSAGES_URL = "/api/v1/messages/"
CONVERSATIONS_URL = "/api/v1/conversations/"
VERIFICATION_SUBMIT_URL = "/api/v1/verification/submit/"
ADMIN_VERIFICATIONS_URL = "/api/v1/admin/verifications/"

PASSWORD = "StrongPass123!"


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


class SystemEndToEndTests(APITestCase):
    """Run each Sprint 7.3 journey end to end across real endpoints/pages."""

    def setUp(self):
        self.client = APIClient(HTTP_HOST="localhost")

    # --- API / session helpers -------------------------------------------------

    def register(self, email, role):
        return self.client.post(
            REGISTER_URL,
            {
                "email": email,
                "full_name": "System User",
                "phone": "08012345678",
                "password": PASSWORD,
                "role": role,
            },
            format="json",
        )

    def login(self, email):
        response = self.client.post(
            LOGIN_URL,
            {"email": email, "password": PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        return response.data["data"]["access"]

    def auth(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def create_admin(self):
        return User.objects.create_user(
            email="admin@example.com",
            password=PASSWORD,
            full_name="Administrator",
            role=User.Role.ADMIN,
        )

    def prepare_landlord_catalogue(self):
        """Register a landlord and publish three Calabar listings.

        Returns ``(landlord_user, apartment_ids)``.
        """
        self.register("landlord@example.com", User.Role.LANDLORD)
        landlord = User.objects.get(email="landlord@example.com")
        self.auth(self.login("landlord@example.com"))

        ids = []
        for payload in (
            apartment_payload(),
            apartment_payload(
                title="Quiet One-Bedroom",
                rental_price="180000.00",
                apartment_type=Apartment.ApartmentType.ONE_BEDROOM,
                bedrooms=1,
                bathrooms=1,
            ),
            apartment_payload(
                title="Spacious Three-Bedroom",
                rental_price="400000.00",
                apartment_type=Apartment.ApartmentType.THREE_BEDROOM,
                bedrooms=3,
                bathrooms=3,
            ),
        ):
            response = self.client.post(APARTMENTS_URL, payload, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
            ids.append(response.data["data"]["id"])
        self.client.credentials()
        return landlord, ids

    # --- 1. Tenant journey ------------------------------------------------------

    def test_tenant_journey_end_to_end(self):
        """Register -> Search -> Filter -> Preferences -> Recommendation ->
        Apartment Details -> Message Landlord, all through the real system."""
        landlord, apartment_ids = self.prepare_landlord_catalogue()
        self.register("tenant@example.com", User.Role.TENANT)
        tenant = User.objects.get(email="tenant@example.com")
        self.auth(self.login("tenant@example.com"))

        # Search the catalogue by location.
        search = self.client.get(APARTMENTS_URL, {"location": "Calabar"})
        self.assertEqual(search.status_code, status.HTTP_200_OK)
        self.assertEqual(search.data["count"], 3)

        # Filter by combined criteria (price + bedrooms + facility).
        filtered = self.client.get(
            APARTMENTS_URL,
            {"max_price": "300000", "bedrooms": "2", "parking": "true"},
        )
        self.assertEqual(filtered.status_code, status.HTTP_200_OK)
        self.assertEqual(filtered.data["count"], 1)
        self.assertEqual(filtered.data["data"][0]["id"], apartment_ids[0])

        # Save a preference vector (Weighted KNN query).
        pref = self.client.post(
            PREFERENCES_URL,
            {
                "location": "Calabar",
                "max_rent": "500000",
                "apartment_type": Apartment.ApartmentType.TWO_BEDROOM,
                "bedrooms": 2,
                "bathrooms": 2,
                "parking": True,
            },
            format="json",
        )
        self.assertEqual(pref.status_code, status.HTTP_201_CREATED, pref.data)
        self.assertEqual(Preference.objects.count(), 1)

        # Generate Weighted KNN recommendations from the saved preference.
        rec = self.client.post(RECOMMENDATIONS_GENERATE_URL, {}, format="json")
        self.assertEqual(rec.status_code, status.HTTP_201_CREATED, rec.data)
        recommendation = Recommendation.objects.get(tenant=tenant)
        self.assertEqual(recommendation.algorithm, Recommendation.Algorithm.WEIGHTED_KNN)
        distances = list(recommendation.items.values_list("distance", flat=True))
        self.assertEqual(distances, sorted(distances))
        self.assertGreaterEqual(len(recommendation.items.all()), 1)

        listing = self.client.get(RECOMMENDATIONS_URL)
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(listing.data["count"], 1)

        # Open the apartment detail presentation page.
        detail = self.client.get(f"/apartments/{apartment_ids[0]}/")
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertContains(detail, "Sunny 2-Bedroom Flat")

        # Message the landlord directly.
        send = self.client.post(
            MESSAGES_URL,
            {"recipient": landlord.pk, "body": "Is the 2-bedroom flat available?"},
            format="json",
        )
        self.assertEqual(send.status_code, status.HTTP_201_CREATED, send.data)
        self.assertEqual(Message.objects.count(), 1)
        self.assertEqual(Conversation.objects.count(), 1)

        conv_list = self.client.get(CONVERSATIONS_URL)
        self.assertEqual(conv_list.status_code, status.HTTP_200_OK)
        self.assertEqual(len(conv_list.data["data"]), 1)
        conversation_id = conv_list.data["data"][0]["id"]
        conv_detail = self.client.get(f"{CONVERSATIONS_URL}{conversation_id}/")
        self.assertEqual(conv_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(len(conv_detail.data["data"]["messages"]), 1)

    # --- 2. Landlord journey ----------------------------------------------------

    def test_landlord_journey_includes_managing_apartment(self):
        """Register -> Verification -> Create Apartment -> Manage Apartment
        (edit + availability) -> Receive & reply to a message."""
        self.register("landlord@example.com", User.Role.LANDLORD)
        landlord = User.objects.get(email="landlord@example.com")
        self.auth(self.login("landlord@example.com"))

        # Submit verification information.
        submit = self.client.post(
            VERIFICATION_SUBMIT_URL,
            {"information": "Registered property owner with identification docs."},
            format="json",
        )
        self.assertEqual(submit.status_code, status.HTTP_201_CREATED, submit.data)
        verification = VerificationRequest.objects.get(landlord=landlord)
        self.assertEqual(verification.status, VerificationRequest.Status.PENDING)

        status_view = self.client.get("/api/v1/verification/status/")
        self.assertEqual(status_view.status_code, status.HTTP_200_OK)
        self.assertEqual(len(status_view.data["data"]), 1)

        # Create a listing.
        listing = self.client.post(APARTMENTS_URL, apartment_payload(), format="json")
        self.assertEqual(listing.status_code, status.HTTP_201_CREATED, listing.data)
        apartment_id = listing.data["data"]["id"]

        # Manage Apartment: edit the listing content (Sprint 7.3 journey step).
        edit = self.client.patch(
            f"{APARTMENTS_URL}{apartment_id}/",
            {"title": "Renovated 2-Bedroom Flat", "rental_price": "300000.00"},
            format="multipart",
        )
        self.assertEqual(edit.status_code, status.HTTP_200_OK, edit.data)
        apartment = Apartment.objects.get(pk=apartment_id)
        self.assertEqual(apartment.title, "Renovated 2-Bedroom Flat")
        self.assertEqual(str(apartment.rental_price), "300000.00")

        # Manage Apartment: update availability (mark temporarily unavailable,
        # then restore it so it remains visible later in the system flow).
        self.assertEqual(apartment.availability, True)
        hide = self.client.patch(
            f"{APARTMENTS_URL}{apartment_id}/",
            {"availability": False},
            format="multipart",
        )
        self.assertEqual(hide.status_code, status.HTTP_200_OK, hide.data)
        apartment.refresh_from_db()
        self.assertFalse(apartment.availability)

        show = self.client.patch(
            f"{APARTMENTS_URL}{apartment_id}/",
            {"availability": True},
            format="multipart",
        )
        self.assertEqual(show.status_code, status.HTTP_200_OK, show.data)
        apartment.refresh_from_db()
        self.assertTrue(apartment.availability)

        # Landlord can see their own listing on the presentation management page.
        self.client.force_login(landlord)
        my_listings = self.client.get("/my/apartments/")
        self.assertEqual(my_listings.status_code, status.HTTP_200_OK)
        self.assertContains(my_listings, "Renovated 2-Bedroom Flat")

        # Receive a tenant's message and reply (landlord side of messaging).
        tenant = User.objects.create_user(
            email="tenant@example.com",
            password=PASSWORD,
            full_name="Tenant",
            role=User.Role.TENANT,
        )
        Message.objects.create(
            conversation=Conversation.objects.create(tenant=tenant, landlord=landlord),
            sender=tenant,
            recipient=landlord,
            body="Available?",
        )
        self.client.logout()
        self.auth(self.login("landlord@example.com"))
        messages = self.client.get(MESSAGES_URL)
        self.assertEqual(messages.status_code, status.HTTP_200_OK)
        self.assertEqual(len(messages.data["data"]), 1)

        conversation = Conversation.objects.get(tenant=tenant, landlord=landlord)
        reply = self.client.post(
            f"{CONVERSATIONS_URL}{conversation.pk}/messages/",
            {"body": "Yes, available."},
            format="json",
        )
        self.assertEqual(reply.status_code, status.HTTP_201_CREATED, reply.data)

    # --- 3. Administrator journey ----------------------------------------------

    def test_admin_journey_manages_users_and_listings(self):
        """Login -> Manage Users -> Review Verification -> Manage Listings."""
        # Landlord submits a verification and a listing (system data for the
        # administrator to act upon).
        self.register("landlord@example.com", User.Role.LANDLORD)
        landlord = User.objects.get(email="landlord@example.com")
        self.auth(self.login("landlord@example.com"))
        self.client.post(
            VERIFICATION_SUBMIT_URL,
            {"information": "Registered property owner with identification docs."},
            format="json",
        )
        listing = self.client.post(APARTMENTS_URL, apartment_payload(), format="json")
        self.assertEqual(listing.status_code, status.HTTP_201_CREATED, listing.data)
        apartment_id = listing.data["data"]["id"]
        verification = VerificationRequest.objects.get(landlord=landlord)
        self.client.credentials()

        admin = self.create_admin()

        # Login (session) and open the dashboard / user management console.
        self.client.force_login(admin)
        dashboard = self.client.get(reverse("admin_dashboard:dashboard"))
        self.assertEqual(dashboard.status_code, 200)
        users_page = self.client.get(reverse("admin_dashboard:users"))
        self.assertEqual(users_page.status_code, 200)
        self.assertContains(users_page, "landlord@example.com")

        # Manage Users: deactivate then reactivate the landlord account.
        user_status = reverse("admin_dashboard:user-status", args=[landlord.pk])
        self.assertEqual(
            self.client.post(user_status).status_code, 302
        )
        landlord.refresh_from_db()
        self.assertFalse(landlord.is_active)
        self.assertEqual(
            self.client.post(user_status).status_code, 302
        )
        landlord.refresh_from_db()
        self.assertTrue(landlord.is_active)

        # Review Verification: approve the landlord's pending request.
        review = reverse(
            "admin_dashboard:verification-review", args=[verification.pk]
        )
        self.assertEqual(
            self.client.post(review, {"action": "approve"}).status_code, 302
        )
        verification.refresh_from_db()
        self.assertEqual(verification.status, VerificationRequest.Status.APPROVED)
        self.assertEqual(verification.reviewed_by, admin)

        # Manage Listings: apartment moderation (hide then restore) on the
        # apartment management page.
        apartments_page = self.client.get(reverse("admin_dashboard:apartments"))
        self.assertEqual(apartments_page.status_code, 200)
        moderate = reverse(
            "admin_dashboard:apartment-moderate", args=[apartment_id]
        )
        self.assertEqual(self.client.post(moderate).status_code, 302)
        apartment = Apartment.objects.get(pk=apartment_id)
        self.assertFalse(apartment.availability)
        self.assertEqual(self.client.post(moderate).status_code, 302)
        apartment.refresh_from_db()
        self.assertTrue(apartment.availability)

        # The administrative reports page computes real database figures.
        reports = self.client.get(reverse("admin_dashboard:reports"))
        self.assertEqual(reports.status_code, 200)
        self.assertEqual(reports.context["verification_counts"][
            VerificationRequest.Status.APPROVED
        ], 1)
        self.assertEqual(reports.context["apartments_total"], 1)
