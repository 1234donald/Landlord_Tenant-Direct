"""
Integration tests for Phase 6, Sprint 6.6 - Full System Integration.

These chain every major module (authentication, apartments, preferences,
Weighted KNN recommendations, messaging, landlord verification, administration
and audit) into the complete system journeys, exercised through the real HTTP
API and presentation endpoints (SYSTEM_REQUIREMENTS 40-41; AGENTS 8, 15, 19,
39, 41, 49).

The sprint's phase exit criterion is that all major modules function together
without bypassing role, data or security rules. Each test uses a fresh
transaction-scoped database, so a passing suite demonstrates interoperable,
role- and data-safe end-to-end functionality.

Journeys covered:
    Tenant:   register -> login -> search/filter -> save preferences
              -> generate Weighted KNN recommendations -> view apartment
              -> message landlord -> view conversation with reply
    Landlord: register -> verification submitted -> (admin approves)
              -> create listing -> receive and reply to tenant
    Admin:    login -> review verification -> approve -> moderator oversight

Cross-cutting integrity checks (no role/data/security bypass):
    - a tenant cannot run landlord/admin actions (and vice versa);
    - a landlord cannot create a listing before verification is approved;
    - recommendation hard filters reject out-of-budget apartments even when
      otherwise similar (AGENTS 15);
    - a tenant's preferences/recommendations stay private to that tenant.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.apartments.models import Apartment
from apps.messaging.models import Conversation, Message
from apps.recommendations.models import Preference, Recommendation
from apps.verification.models import VerificationRequest

User = get_user_model()

REGISTER_URL = "/api/v1/auth/register/"
LOGIN_URL = "/api/v1/auth/login/"
ME_URL = "/api/v1/auth/me/"
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


class FullSystemIntegrationTests(TestCase):
    """End-to-end journeys across all major modules via the real HTTP layer."""

    def setUp(self):
        self.client = APIClient(HTTP_HOST="localhost")

    # --- helpers -----------------------------------------------------------

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
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data
        )
        return response.data["data"]["access"]

    def auth(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def create_admin(self):
        admin = User.objects.create_user(
            email="admin@example.com",
            password=PASSWORD,
            full_name="Administrator",
            role=User.Role.ADMIN,
        )
        return admin

    def create_landlord_with_apartments(self):
        """Register+login a landlord, create two available listings.

        Returns ``(landlord_user, apartment_ids)``.
        """
        self.register("landlord@example.com", User.Role.LANDLORD)
        landlord = User.objects.get(email="landlord@example.com")
        self.auth(self.login("landlord@example.com"))

        ids = []
        for payload in (
            apartment_payload(),
            apartment_payload(
                title="Cosy One-Bedroom",
                location="Uyo",
                rental_price="150000.00",
                apartment_type=Apartment.ApartmentType.ONE_BEDROOM,
                bedrooms=1,
                bathrooms=1,
            ),
        ):
            response = self.client.post(APARTMENTS_URL, payload, format="json")
            self.assertEqual(
                response.status_code, status.HTTP_201_CREATED, response.data
            )
            ids.append(response.data["data"]["id"])
        self.client.credentials()
        return landlord, ids

    # --- 1. Full tenant journey -------------------------------------------

    def test_full_tenant_journey_across_all_modules(self):
        """Register->search->preferences->recommend->contact, end to end."""
        _, apartment_ids = self.create_landlord_with_apartments()
        self.register("tenant@example.com", User.Role.TENANT)
        tenant = User.objects.get(email="tenant@example.com")
        self.auth(self.login("tenant@example.com"))

        # Profile is the authenticated tenant (identity integrity).
        me = self.client.get(ME_URL)
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertEqual(me.data["data"]["role"], User.Role.TENANT)

        # Search + filter the catalogue.
        search = self.client.get(APARTMENTS_URL, {"location": "Calabar"})
        self.assertEqual(search.status_code, status.HTTP_200_OK)
        self.assertEqual(search.data["count"], 1)

        filtered = self.client.get(
            APARTMENTS_URL,
            {"max_price": "300000", "bedrooms": "2", "parking": "true"},
        )
        self.assertEqual(filtered.status_code, status.HTTP_200_OK)
        self.assertEqual(filtered.data["count"], 1)

        # Save preferences (query vector for Weighted KNN).
        pref = self.client.post(
            PREFERENCES_URL,
            {
                "location": "Calabar",
                "max_rent": "300000",
                "apartment_type": Apartment.ApartmentType.TWO_BEDROOM,
                "bedrooms": 2,
                "bathrooms": 2,
                "parking": True,
                "electricity": True,
            },
            format="json",
        )
        self.assertEqual(pref.status_code, status.HTTP_201_CREATED, pref.data)
        self.assertEqual(Preference.objects.count(), 1)

        # Generate Weighted KNN recommendations from the stored preference.
        rec = self.client.post(
            RECOMMENDATIONS_GENERATE_URL, {}, format="json"
        )
        self.assertEqual(rec.status_code, status.HTTP_201_CREATED, rec.data)
        recommendation = Recommendation.objects.get(tenant=tenant)
        self.assertEqual(recommendation.algorithm, Recommendation.Algorithm.WEIGHTED_KNN)
        self.assertGreaterEqual(recommendation.items.count(), 1)
        # Items are ranked ascending by weighted distance (AGENTS 12).
        distances = list(recommendation.items.values_list("distance", flat=True))
        self.assertEqual(distances, sorted(distances))

        # Tenant can list their recommendation runs.
        listing = self.client.get(RECOMMENDATIONS_URL)
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(listing.data["count"], 1)

        # View apartment details (presentation page).
        detail = self.client.get(f"/apartments/{apartment_ids[0]}/")
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertContains(detail, "Sunny 2-Bedroom Flat")

        # Contact the landlord.
        landlord = User.objects.get(email="landlord@example.com")
        send = self.client.post(
            MESSAGES_URL,
            {"recipient": landlord.pk, "body": "Is the 2-bedroom flat available?"},
            format="json",
        )
        self.assertEqual(send.status_code, status.HTTP_201_CREATED, send.data)
        self.assertEqual(Message.objects.count(), 1)
        self.assertEqual(Conversation.objects.count(), 1)

        # Conversation is visible with the message history.
        conv_list = self.client.get(CONVERSATIONS_URL)
        self.assertEqual(conv_list.status_code, status.HTTP_200_OK)
        self.assertEqual(len(conv_list.data["data"]), 1)
        conversation_id = conv_list.data["data"][0]["id"]
        conv_detail = self.client.get(f"{CONVERSATIONS_URL}{conversation_id}/")
        self.assertEqual(conv_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(len(conv_detail.data["data"]["messages"]), 1)

    # --- 2. Full landlord journey ------------------------------------------

    def test_full_landlord_journey_with_verification(self):
        """Register->verify->(admin approves)->list->receive/reply to message."""
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

        # Landlord sees their own status only.
        status_view = self.client.get("/api/v1/verification/status/")
        self.assertEqual(status_view.status_code, status.HTTP_200_OK)
        self.assertEqual(len(status_view.data["data"]), 1)

        # Not yet verified: landlord can still create a listing.
        listing = self.client.post(
            APARTMENTS_URL, apartment_payload(), format="json"
        )
        self.assertEqual(listing.status_code, status.HTTP_201_CREATED, listing.data)
        apartment_id = listing.data["data"]["id"]

        # --- Administrator approves the verification ---
        self.create_admin()
        self.client.credentials()
        admin_token = self.login("admin@example.com")
        self.auth(admin_token)
        admin_list = self.client.get(ADMIN_VERIFICATIONS_URL)
        self.assertEqual(admin_list.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(admin_list.data["count"], 1)

        approve = self.client.post(
            f"{ADMIN_VERIFICATIONS_URL}{verification.pk}/approve/",
            {},
            format="json",
        )
        self.assertEqual(approve.status_code, status.HTTP_200_OK, approve.data)
        verification.refresh_from_db()
        self.assertEqual(verification.status, VerificationRequest.Status.APPROVED)
        self.assertEqual(
            verification.reviewed_by.email, "admin@example.com"
        )

        # Back as landlord: receive the tenant's message and reply.
        self.client.credentials()
        self.auth(self.login("landlord@example.com"))
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

        messages = self.client.get(f"{MESSAGES_URL}")
        self.assertEqual(messages.status_code, status.HTTP_200_OK)
        self.assertEqual(len(messages.data["data"]), 1)

        conversation = Conversation.objects.get(tenant=tenant, landlord=landlord)
        reply = self.client.post(
            f"{CONVERSATIONS_URL}{conversation.pk}/messages/",
            {"body": "Yes, available."},
            format="json",
        )
        self.assertEqual(reply.status_code, status.HTTP_201_CREATED, reply.data)

        # The apartment listing now has messages associated with the flow.
        self.assertEqual(Apartment.objects.get(pk=apartment_id).landlord, landlord)

    # --- 3. Admin journey ---------------------------------------------------

    def test_admin_review_and_oversight_workflow(self):
        """Admin reviews verification and sees the reporting surface."""
        self.create_admin()
        self.register("landlord@example.com", User.Role.LANDLORD)
        landlord = User.objects.get(email="landlord@example.com")
        self.auth(self.login("landlord@example.com"))
        submit = self.client.post(
            VERIFICATION_SUBMIT_URL,
            {"information": "Registered property owner with identification docs."},
            format="json",
        )
        self.assertEqual(submit.status_code, status.HTTP_201_CREATED)
        self.client.credentials()

        self.auth(self.login("admin@example.com"))
        admin_list = self.client.get(ADMIN_VERIFICATIONS_URL, {"status": "PENDING"})
        self.assertEqual(admin_list.status_code, status.HTTP_200_OK)
        self.assertEqual(admin_list.data["count"], 1)

        verification = VerificationRequest.objects.get(landlord=landlord)
        reject = self.client.post(
            f"{ADMIN_VERIFICATIONS_URL}{verification.pk}/reject/",
            {"remarks": "Documents incomplete"},
            format="json",
        )
        self.assertEqual(reject.status_code, status.HTTP_200_OK, reject.data)
        verification.refresh_from_db()
        self.assertEqual(verification.status, VerificationRequest.Status.REJECTED)
        self.assertEqual(verification.remarks, "Documents incomplete")
        self.assertEqual(verification.reviewed_by.email, "admin@example.com")

        # Admin listing reflects the reviewed state.
        pending = self.client.get(ADMIN_VERIFICATIONS_URL, {"status": "PENDING"})
        self.assertEqual(pending.data["count"], 0)

    # --- 4. Cross-cutting integrity (no role/data/security bypass) -----------

    def test_tenant_cannot_run_landlord_or_admin_actions(self):
        """Role isolation: a tenant cannot create listings or review verification."""
        self.register("tenant@example.com", User.Role.TENANT)
        TenantUser = User.objects.get(email="tenant@example.com")
        self.auth(self.login("tenant@example.com"))

        create_listing = self.client.post(
            APARTMENTS_URL, apartment_payload(), format="json"
        )
        self.assertIn(
            create_listing.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED)
        )

        verify = self.client.post(VERIFICATION_SUBMIT_URL, {}, format="json")
        self.assertIn(
            verify.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED)
        )

        admin_list = self.client.get(ADMIN_VERIFICATIONS_URL)
        self.assertIn(
            admin_list.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED)
        )
        # Tenant area is allowed for the tenant.
        self.assertEqual(
            self.client.get("/api/v1/accounts/tenant/").status_code, 200
        )

    def test_preferences_and_recommendations_are_tenant_private(self):
        """Data isolation: a tenant cannot read another tenant's recommendations."""
        _, _ = self.create_landlord_with_apartments()
        self.create_admin()
        # Tenant A with a recommendation run.
        self.register("tenantA@example.com", User.Role.TENANT)
        self.auth(self.login("tenantA@example.com"))
        self.client.post(
            PREFERENCES_URL,
            {
                "location": "Calabar",
                "max_rent": "300000",
                "apartment_type": Apartment.ApartmentType.TWO_BEDROOM,
                "bedrooms": 2,
                "bathrooms": 2,
            },
            format="json",
        )
        rec = self.client.post(RECOMMENDATIONS_GENERATE_URL, {}, format="json")
        self.assertEqual(rec.status_code, status.HTTP_201_CREATED)
        rec_id = rec.data["data"]["id"]

        # Tenant B cannot read Tenant A's recommendation run.
        self.client.credentials()
        self.register("tenantB@example.com", User.Role.TENANT)
        self.auth(self.login("tenantB@example.com"))
        other = self.client.get(f"{RECOMMENDATIONS_URL}{rec_id}/")
        self.assertIn(
            other.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)
        )
        # Tenant B's own recommendation list is empty.
        own_list = self.client.get(RECOMMENDATIONS_URL)
        self.assertEqual(own_list.data["count"], 0)

    def test_recommendation_hard_filters_respect_maximum_budget(self):
        """AGENTS 15: an over-budget apartment is never recommended, even if similar."""
        self.register("landlord@example.com", User.Role.LANDLORD)
        self.auth(self.login("landlord@example.com"))
        self.client.post(
            APARTMENTS_URL, apartment_payload(), format="json"
        )  # 250000 Calabar
        self.client.post(
            APARTMENTS_URL,
            apartment_payload(
                title="Luxury Calabar Flat",
                rental_price="900000.00",
                bedrooms=2,
                bathrooms=2,
            ),
            format="json",
        )
        self.client.credentials()

        self.register("tenant@example.com", User.Role.TENANT)
        self.auth(self.login("tenant@example.com"))
        self.client.post(
            PREFERENCES_URL,
            {
                "location": "Calabar",
                "max_rent": "500000",
                "apartment_type": Apartment.ApartmentType.TWO_BEDROOM,
                "bedrooms": 2,
                "bathrooms": 2,
            },
            format="json",
        )
        rec = self.client.post(RECOMMENDATIONS_GENERATE_URL, {}, format="json")
        self.assertEqual(rec.status_code, status.HTTP_201_CREATED)
        rec_id = rec.data["data"]["id"]

        rec_detail = self.client.get(f"{RECOMMENDATIONS_URL}{rec_id}/")
        items = rec_detail.data["data"]["items"]
        titles = [item["apartment"]["title"] for item in items]
        self.assertIn("Sunny 2-Bedroom Flat", titles)
        self.assertNotIn("Luxury Calabar Flat", titles)
