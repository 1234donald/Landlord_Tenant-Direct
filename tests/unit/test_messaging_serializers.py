"""
Unit tests for Phase 7, Sprint 7.1 - Messaging serializers.

These construct the DRF serializers directly and verify the conversation
membership rule (one tenant + one distinct landlord), message body validation,
self-message rejection, conversation reuse, and the read representations
(sender/recipient emails, nested participants, last-message helper) without the
HTTP layer (SYSTEM_REQUIREMENTS 41, AGENTS 8, 23).
"""
import django.test as django_tests
from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.messaging.models import Conversation, Message
from apps.messaging.serializers import (
    ConversationSerializer,
    ConversationSummarySerializer,
    MessageCreateSerializer,
    MessageSerializer,
    ParticipantSerializer,
    validate_conversation_pair,
)

User = get_user_model()
PASSWORD = "StrongPass123!"


def make_user(email, role):
    return User.objects.create_user(
        email=email,
        password=PASSWORD,
        full_name=email,
        role=role,
    )


class _FakeRequest:
    def __init__(self, user):
        self.user = user


class ConversationMembershipValidatorTests(django_tests.TestCase):
    def setUp(self):
        self.tenant = make_user("tenant@example.com", User.Role.TENANT)
        self.landlord = make_user("landlord@example.com", User.Role.LANDLORD)

    def test_valid_tenant_landlord_pair_passes(self):
        validate_conversation_pair(self.tenant, self.landlord)

    def test_none_participant_is_rejected(self):
        with self.assertRaises(serializers.ValidationError):
            validate_conversation_pair(None, self.landlord)
        with self.assertRaises(serializers.ValidationError):
            validate_conversation_pair(self.tenant, None)

    def test_same_user_as_both_participants_is_rejected(self):
        with self.assertRaises(serializers.ValidationError):
            validate_conversation_pair(self.tenant, self.tenant)

    def test_tenant_must_be_tenant_role(self):
        other_landlord = make_user("l2@example.com", User.Role.LANDLORD)
        with self.assertRaises(serializers.ValidationError):
            validate_conversation_pair(other_landlord, self.landlord)

    def test_landlord_must_be_landlord_role(self):
        other_tenant = make_user("t2@example.com", User.Role.TENANT)
        with self.assertRaises(serializers.ValidationError):
            validate_conversation_pair(self.tenant, other_tenant)


class MessageCreateSerializerTests(django_tests.TestCase):
    def setUp(self):
        self.tenant = make_user("tenant@example.com", User.Role.TENANT)
        self.landlord = make_user("landlord@example.com", User.Role.LANDLORD)

    def _serializer(self, sender, data):
        return MessageCreateSerializer(
            data=data, context={"request": _FakeRequest(sender)}
        )

    def test_valid_message_between_tenant_and_landlord(self):
        serializer = self._serializer(
            self.tenant,
            {"recipient": self.landlord.pk, "body": "Is it available?"},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        message = serializer.save()
        self.assertEqual(message.sender, self.tenant)
        self.assertEqual(message.recipient, self.landlord)
        self.assertEqual(message.body, "Is it available?")

    def test_reverse_direction_landlord_to_tenant(self):
        serializer = self._serializer(
            self.landlord,
            {"recipient": self.tenant.pk, "body": "Yes."},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        message = serializer.save()
        self.assertEqual(message.sender, self.landlord)
        self.assertEqual(message.recipient, self.tenant)

    def test_message_to_self_is_rejected(self):
        serializer = self._serializer(
            self.tenant,
            {"recipient": self.tenant.pk, "body": "Hi me"},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("recipient", serializer.errors)

    def test_message_between_two_tenants_is_rejected(self):
        other_tenant = make_user("t2@example.com", User.Role.TENANT)
        serializer = self._serializer(
            self.tenant,
            {"recipient": other_tenant.pk, "body": "hello"},
        )
        self.assertFalse(serializer.is_valid())

    def test_blank_body_is_rejected(self):
        serializer = self._serializer(
            self.tenant, {"recipient": self.landlord.pk, "body": "   "}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("body", serializer.errors)

    def test_oversized_body_is_rejected(self):
        serializer = self._serializer(
            self.tenant,
            {"recipient": self.landlord.pk, "body": "x" * 5001},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("body", serializer.errors)

    def test_reuses_existing_conversation(self):
        conversation = Conversation.objects.create(
            tenant=self.tenant, landlord=self.landlord
        )
        serializer = self._serializer(
            self.tenant,
            {"recipient": self.landlord.pk, "body": "hello again"},
        )
        self.assertTrue(serializer.is_valid())
        message = serializer.save()
        self.assertEqual(message.conversation, conversation)
        self.assertEqual(Conversation.objects.count(), 1)

    def test_creates_conversation_when_none_exists(self):
        serializer = self._serializer(
            self.tenant,
            {"recipient": self.landlord.pk, "body": "first contact"},
        )
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assertEqual(Conversation.objects.count(), 1)
        self.assertEqual(Message.objects.count(), 1)


class ConversationMessageOnlySerializerTests(django_tests.TestCase):
    def test_read_message_serializer_exposes_emails(self):
        tenant = make_user("tenant@example.com", User.Role.TENANT)
        landlord = make_user("landlord@example.com", User.Role.LANDLORD)
        conversation = Conversation.objects.create(tenant=tenant, landlord=landlord)
        message = Message.objects.create(
            conversation=conversation,
            sender=tenant,
            recipient=landlord,
            body="hello",
        )
        data = MessageSerializer(message).data
        self.assertEqual(data["sender_email"], tenant.email)
        self.assertEqual(data["recipient_email"], landlord.email)

    def test_participant_serializer_is_compact(self):
        tenant = make_user("tenant@example.com", User.Role.TENANT)
        data = ParticipantSerializer(tenant).data
        self.assertEqual(
            set(data.keys()), {"id", "email", "full_name", "role"}
        )

    def test_conversation_serializer_nests_details_and_messages(self):
        tenant = make_user("tenant@example.com", User.Role.TENANT)
        landlord = make_user("landlord@example.com", User.Role.LANDLORD)
        conversation = Conversation.objects.create(tenant=tenant, landlord=landlord)
        Message.objects.create(
            conversation=conversation, sender=tenant,
            recipient=landlord, body="one",
        )
        data = ConversationSerializer(conversation).data
        self.assertEqual(data["tenant_detail"]["email"], tenant.email)
        self.assertEqual(data["landlord_detail"]["email"], landlord.email)
        self.assertEqual(len(data["messages"]), 1)

    def test_conversation_summary_last_message_present(self):
        tenant = make_user("tenant@example.com", User.Role.TENANT)
        landlord = make_user("landlord@example.com", User.Role.LANDLORD)
        conversation = Conversation.objects.create(tenant=tenant, landlord=landlord)
        Message.objects.create(
            conversation=conversation, sender=tenant,
            recipient=landlord, body="latest",
        )
        data = ConversationSummarySerializer(conversation).data
        self.assertEqual(data["last_message"]["body"], "latest")

    def test_conversation_summary_last_message_none_when_empty(self):
        tenant = make_user("tenant@example.com", User.Role.TENANT)
        landlord = make_user("landlord@example.com", User.Role.LANDLORD)
        conversation = Conversation.objects.create(tenant=tenant, landlord=landlord)
        data = ConversationSummarySerializer(conversation).data
        self.assertIsNone(data["last_message"])
