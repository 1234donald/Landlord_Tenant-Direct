"""
Integration tests for Phase 4, Sprint 4.6 - Tenant Journey Integration.

These chain the tenant-facing modules into one end-to-end journey:

    Tenant -> Search -> Filter -> View Apartment -> Save Preferences
        -> Contact Landlord

The test performs the flow through the real HTTP API and presentation pages,
verifying that the modules (authentication, apartment search/filter/details,
tenant preferences and messaging) interoperate correctly and that the phase
exit criteria for Sprint 4.6 are met. No new UI is required; this sprint wires
and verifies the existing building blocks (AGENTS 8, 21).
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.apartments.models import Apartment
from apps.messaging.models import Conversation, Message
from apps.recommendations.models import Preference

User = get_user_model()

REGISTER_URL = "/api/v1/auth/register/"
LOGIN_URL = "/api/v1/auth/login/"
APARTMENTS_URL = "/api/v1/apartments/"
PREFERENCES_URL = "/api/v1/preferences/"
MESSAGES_URL = "/api/v1/messages/"
CONVERSATIONS_URL = "/api/v1/conversations/"

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


class TenantJourneyIntegrationTests(TestCase):
    """Exercise the full Sprint 4.6 tenant journey end to end.

    Each test uses a fresh transaction-scoped database and drives the real HTTP
    API/presentation endpoints, so a passing suite demonstrates the tenant flow
    (phase exit criteria) works with all modules cooperating.
    """

    def setUp(self):
        self.client = APIClient(HTTP_HOST="localhost")

    def register(self, email, role):
        return self.client.post(
            REGISTER_URL,
            {
                "email": email,
                "full_name": "Journey User",
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
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data["data"]["access"]

    def auth(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def create_landlord_with_apartments(self):
        """Register+login a landlord and create two available listings.

        Returns ``(landlord_user, apartment_ids)``.
        """
        self.register("landlord@example.com", User.Role.LANDLORD)
        landlord = User.objects.get(email="landlord@example.com")
        landlord_token = self.login("landlord@example.com")
        self.auth(landlord_token)

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
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            ids.append(response.data["data"]["id"])
        self.client.credentials()
        return landlord, ids

    def prepare_tenant(self):
        """Register+login a tenant and return ``(tenant_user, token)``."""
        self.register("tenant@example.com", User.Role.TENANT)
        tenant = User.objects.get(email="tenant@example.com")
        token = self.login("tenant@example.com")
        return tenant, token

    # --- Full journey ---

    def test_full_tenant_journey(self):
        """The whole journey: search, filter, view, save preferences, contact."""
        _, apartment_ids = self.create_landlord_with_apartments()
        tenant, tenant_token = self.prepare_tenant()
        self.auth(tenant_token)

        # Search by location (Calabar).
        response = self.client.get(APARTMENTS_URL, {"location": "Calabar"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

        # Filter: combined criteria (price range + bedrooms + facilities).
        response = self.client.get(
            APARTMENTS_URL,
            {
                "max_price": "300000",
                "bedrooms": "2",
                "parking": "true",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

        # View apartment details (presentation page).
        detail = self.client.get(f"/apartments/{apartment_ids[0]}/")
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertContains(detail, "Sunny 2-Bedroom Flat")

        # Save preferences as the tenant.
        pref_response = self.client.post(
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
        self.assertEqual(pref_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Preference.objects.count(), 1)
        own_preference = Preference.objects.get(tenant=tenant)
        self.assertEqual(own_preference.max_rent, 300000)

        # Contact landlord: send a message.
        landlord = User.objects.get(email="landlord@example.com")
        message_response = self.client.post(
            MESSAGES_URL,
            {"recipient": landlord.pk, "body": "Is the 2-bedroom flat available?"},
            format="json",
        )
        self.assertEqual(message_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Message.objects.count(), 1)
        self.assertEqual(Conversation.objects.count(), 1)

        # Tenant can see the conversation and its message history.
        conv_list = self.client.get(CONVERSATIONS_URL)
        self.assertEqual(conv_list.status_code, status.HTTP_200_OK)
        self.assertEqual(len(conv_list.data["data"]), 1)
        conversation_id = conv_list.data["data"][0]["id"]
        conv_detail = self.client.get(f"{CONVERSATIONS_URL}{conversation_id}/")
        self.assertEqual(conv_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(len(conv_detail.data["data"]["messages"]), 1)

    # --- Supporting flow checks ---

    def test_journey_requires_an_authenticated_tenant_for_preferences(self):
        _, _ = self.create_landlord_with_apartments()
        self.prepare_tenant()
        # Unauthenticated preference save must be rejected.
        response = self.client.post(
            PREFERENCES_URL,
            {"location": "Calabar"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unavailable_apartments_are_hidden_from_browse_page(self):
        _, apartment_ids = self.create_landlord_with_apartments()
        # Mark the Calabar apartment unavailable directly in the DB.
        Apartment.objects.filter(pk=apartment_ids[0]).update(availability=False)

        # The presentation browse page hides unavailable listings.
        response = self.client.get("/apartments/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Cosy One-Bedroom")
        self.assertNotContains(response, "Sunny 2-Bedroom Flat")

    def test_landlord_receives_tenant_message_and_can_reply(self):
        _, _ = self.create_landlord_with_apartments()
        tenant, tenant_token = self.prepare_tenant()
        self.auth(tenant_token)

        landlord = User.objects.get(email="landlord@example.com")
        send = self.client.post(
            MESSAGES_URL,
            {"recipient": landlord.pk, "body": "Is it available?"},
            format="json",
        )
        self.assertEqual(send.status_code, status.HTTP_201_CREATED)

        # The landlord sees the incoming message as its recipient.
        landlord_token = self.login("landlord@example.com")
        self.auth(landlord_token)
        messages = self.client.get(MESSAGES_URL)
        self.assertEqual(messages.status_code, status.HTTP_200_OK)
        self.assertEqual(len(messages.data["data"]), 1)
        self.assertEqual(messages.data["data"][0]["recipient"], landlord.pk)

        # Landlord replies through the conversation.
        conversation = Conversation.objects.get()
        reply = self.client.post(
            f"{CONVERSATIONS_URL}{conversation.pk}/messages/",
            {"body": "Yes, still available."},
            format="json",
        )
        self.assertEqual(reply.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Message.objects.count(), 2)
