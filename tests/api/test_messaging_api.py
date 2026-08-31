"""
API tests for Phase 4, Sprint 4.5 - Messaging and Conversations.

These verify the Messaging API (§24.5): send/receive messages, conversation
history, message status and participant permission restrictions. A user may only
see conversations they belong to and messages they sent or received; only a
tenant and a landlord may converse; an administrator has full access.
"""
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.messaging.models import Conversation, Message

User = get_user_model()

LOGIN_URL = "/api/v1/auth/login/"
MESSAGES_URL = "/api/v1/messages/"
CONVERSATIONS_URL = "/api/v1/conversations/"

PASSWORD = "StrongPass123!"


class MessagingApiTests(APITestCase):
    def setUp(self):
        self.client = APIClient(HTTP_HOST="localhost")
        self.tenant = User.objects.create_user(
            email="tenant@example.com",
            password=PASSWORD,
            full_name="Tenant User",
            role=User.Role.TENANT,
        )
        self.landlord = User.objects.create_user(
            email="landlord@example.com",
            password=PASSWORD,
            full_name="Landlord User",
            role=User.Role.LANDLORD,
        )
        self.other_tenant = User.objects.create_user(
            email="other@example.com",
            password=PASSWORD,
            full_name="Other Tenant",
            role=User.Role.TENANT,
        )
        self.other_landlord = User.objects.create_user(
            email="otherlandlord@example.com",
            password=PASSWORD,
            full_name="Other Landlord",
            role=User.Role.LANDLORD,
        )
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password=PASSWORD,
            full_name="Admin User",
            role=User.Role.ADMIN,
        )

    def _auth_as(self, user):
        response = self.client.post(
            LOGIN_URL,
            {"email": user.email, "password": PASSWORD},
            format="json",
        )
        access = response.data["data"]["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def _make_conversation(self):
        return Conversation.objects.create(
            tenant=self.tenant,
            landlord=self.landlord,
        )

    def _make_message(self, conversation=None, sender=None, recipient=None, body="Hi."):
        conversation = conversation or self._make_conversation()
        return Message.objects.create(
            conversation=conversation,
            sender=sender or self.tenant,
            recipient=recipient or self.landlord,
            body=body,
        )

    # --- Send a message (POST /messages/) ---

    def _send(self, recipient, body):
        return self.client.post(
            MESSAGES_URL,
            {"recipient": recipient.pk, "body": body},
            format="json",
        )

    def test_tenant_can_send_message_to_landlord(self):
        self._auth_as(self.tenant)
        response = self._send(self.landlord, "Good morning")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        data = response.data["data"]
        self.assertEqual(data["sender"], self.tenant.pk)
        self.assertEqual(data["recipient"], self.landlord.pk)
        self.assertEqual(data["body"], "Good morning")
        self.assertEqual(Message.objects.count(), 1)
        self.assertEqual(Conversation.objects.count(), 1)

    def test_landlord_can_send_message_to_tenant(self):
        self._auth_as(self.landlord)
        response = self._send(self.tenant, "I received your enquiry")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.data["data"]
        self.assertEqual(data["sender"], self.landlord.pk)
        self.assertEqual(data["recipient"], self.tenant.pk)

    def test_sending_again_reuses_conversation(self):
        self._auth_as(self.tenant)
        self._send(self.landlord, "First")
        self._send(self.landlord, "Second")
        self.assertEqual(Conversation.objects.count(), 1)
        self.assertEqual(Message.objects.count(), 2)

    def test_rejects_empty_body(self):
        self._auth_as(self.tenant)
        response = self._send(self.landlord, "   ")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("body", response.data["errors"])

    def test_rejects_messaging_self(self):
        self._auth_as(self.tenant)
        response = self._send(self.tenant, "Hello me")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_tenant_cannot_message_another_tenant(self):
        self._auth_as(self.tenant)
        response = self._send(self.other_tenant, "Hey")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_cannot_send_message(self):
        response = self._send(self.landlord, "Hi")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- List messages (GET /messages/) ---

    def test_list_returns_only_own_messages(self):
        conversation = self._make_conversation()
        self._make_message(conversation, sender=self.tenant, recipient=self.landlord)
        self._make_message(
            conversation,
            sender=self.other_tenant,
            recipient=self.other_landlord,
        )
        self._auth_as(self.tenant)
        response = self.client.get(MESSAGES_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["sender"], self.tenant.pk)

    def test_landlord_sees_received_message(self):
        self._make_message(sender=self.tenant, recipient=self.landlord)
        self._auth_as(self.landlord)
        response = self.client.get(MESSAGES_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 1)

    def test_admin_lists_all_messages(self):
        self._make_message(sender=self.tenant, recipient=self.landlord)
        other_conversation = Conversation.objects.create(
            tenant=self.other_tenant,
            landlord=self.other_landlord,
        )
        self._make_message(
            conversation=other_conversation,
            sender=self.other_tenant,
            recipient=self.other_landlord,
        )
        self._auth_as(self.admin)
        response = self.client.get(MESSAGES_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 2)

    # --- Retrieve message (GET /messages/{id}/) ---

    def test_sender_can_retrieve_message(self):
        message = self._make_message(sender=self.tenant, recipient=self.landlord)
        self._auth_as(self.tenant)
        response = self.client.get(f"{MESSAGES_URL}{message.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["id"], message.pk)

    def test_recipient_can_retrieve_message(self):
        message = self._make_message(sender=self.tenant, recipient=self.landlord)
        self._auth_as(self.landlord)
        response = self.client.get(f"{MESSAGES_URL}{message.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_outsider_cannot_retrieve_message(self):
        message = self._make_message(sender=self.tenant, recipient=self.landlord)
        self._auth_as(self.other_tenant)
        response = self.client.get(f"{MESSAGES_URL}{message.pk}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_recipient_retrieval_marks_message_read(self):
        message = self._make_message(sender=self.tenant, recipient=self.landlord)
        self._auth_as(self.landlord)
        response = self.client.get(f"{MESSAGES_URL}{message.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["status"], Message.Status.READ)

    def test_admin_can_retrieve_any_message(self):
        message = self._make_message(sender=self.tenant, recipient=self.landlord)
        self._auth_as(self.admin)
        response = self.client.get(f"{MESSAGES_URL}{message.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # --- Conversations (GET /conversations/, POST /conversations/) ---

    def test_list_conversations_returns_only_participled(self):
        self._make_conversation()
        Conversation.objects.create(
            tenant=self.other_tenant,
            landlord=self.other_landlord,
        )
        self._auth_as(self.tenant)
        response = self.client.get(CONVERSATIONS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["tenant"], self.tenant.pk)

    def test_admin_can_list_all_conversations(self):
        self._make_conversation()
        self._auth_as(self.admin)
        response = self.client.get(CONVERSATIONS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 1)

    def test_create_conversation_with_landlord(self):
        self._auth_as(self.tenant)
        response = self.client.post(
            CONVERSATIONS_URL,
            {"counterpart": self.landlord.pk},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Conversation.objects.count(), 1)

    def test_create_conversation_without_counterpart_returns_400(self):
        self._auth_as(self.tenant)
        response = self.client.post(CONVERSATIONS_URL, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("counterpart", response.data["errors"])

    def test_create_conversation_with_same_role_counterpart_returns_400(self):
        self._auth_as(self.tenant)
        response = self.client.post(
            CONVERSATIONS_URL,
            {"counterpart": self.other_tenant.pk},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("counterpart", response.data["errors"])

    # --- Conversation detail (GET /conversations/{id}/) ---

    def test_participant_can_retrieve_conversation_history(self):
        conversation = self._make_conversation()
        self._make_message(conversation, sender=self.tenant, recipient=self.landlord)
        self._make_message(conversation, sender=self.landlord, recipient=self.tenant)
        self._auth_as(self.tenant)
        response = self.client.get(f"{CONVERSATIONS_URL}{conversation.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        self.assertEqual(len(data["messages"]), 2)

    def test_outsider_cannot_retrieve_conversation(self):
        conversation = self._make_conversation()
        self._auth_as(self.other_tenant)
        response = self.client.get(f"{CONVERSATIONS_URL}{conversation.pk}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieving_conversation_marks_incoming_as_read(self):
        conversation = self._make_conversation()
        self._make_message(conversation, sender=self.landlord, recipient=self.tenant)
        self._auth_as(self.tenant)
        response = self.client.get(f"{CONVERSATIONS_URL}{conversation.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["data"]["messages"][0]["status"],
            Message.Status.READ,
        )

    def test_admin_can_retrieve_any_conversation(self):
        conversation = self._make_conversation()
        self._auth_as(self.admin)
        response = self.client.get(f"{CONVERSATIONS_URL}{conversation.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # --- Send within conversation (POST /conversations/{id}/messages/) ---

    def test_participant_can_send_in_conversation(self):
        conversation = self._make_conversation()
        self._auth_as(self.tenant)
        response = self.client.post(
            f"{CONVERSATIONS_URL}{conversation.pk}/messages/",
            {"body": "Following up"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.data["data"]
        self.assertEqual(data["conversation"], conversation.pk)
        self.assertEqual(data["sender"], self.tenant.pk)
        self.assertEqual(data["recipient"], self.landlord.pk)

    def test_outsider_cannot_send_in_conversation(self):
        conversation = self._make_conversation()
        self._auth_as(self.other_tenant)
        response = self.client.post(
            f"{CONVERSATIONS_URL}{conversation.pk}/messages/",
            {"body": "Intruding"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_missing_conversation_returns_404(self):
        self._auth_as(self.tenant)
        response = self.client.get(f"{CONVERSATIONS_URL}99999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
