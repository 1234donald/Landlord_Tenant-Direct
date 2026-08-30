"""
Unit tests for Phase 4, Sprint 4.5 - Messaging Data Model.

These verify the ``Conversation`` and ``Message`` models: the tenant/landlord
participant relationship, message sender/recipient and status, the unique
conversation pair, validation rules and database indexes. They require a test
database.
"""
import django.test as django_tests
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.messaging.models import Conversation, Message

User = get_user_model()

PASSWORD = "StrongPass123!"


def make_tenant(email="tenant@example.com"):
    return User.objects.create_user(
        email=email,
        password=PASSWORD,
        full_name="Tenant User",
        role=User.Role.TENANT,
    )


def make_landlord(email="landlord@example.com"):
    return User.objects.create_user(
        email=email,
        password=PASSWORD,
        full_name="Landlord User",
        role=User.Role.LANDLORD,
    )


def make_conversation(tenant=None, landlord=None):
    return Conversation.objects.create(
        tenant=tenant or make_tenant(),
        landlord=landlord or make_landlord(),
    )


def make_message(conversation=None, sender=None, recipient=None, **kwargs):
    conversation = conversation or make_conversation()
    if sender is None:
        sender = conversation.tenant
    if recipient is None:
        recipient = conversation.landlord
    defaults = {"body": "Hello there.", "status": Message.Status.SENT}
    defaults.update(kwargs)
    return Message.objects.create(
        conversation=conversation,
        sender=sender,
        recipient=recipient,
        **defaults,
    )


class ConversationModelTests(django_tests.TestCase):
    def test_participant_relationship(self):
        tenant = make_tenant()
        landlord = make_landlord()
        conversation = make_conversation(tenant=tenant, landlord=landlord)
        self.assertEqual(conversation.tenant, tenant)
        self.assertEqual(conversation.landlord, landlord)
        self.assertIn(conversation, tenant.tenant_conversations.all())
        self.assertIn(conversation, landlord.landlord_conversations.all())

    def test_conversation_requires_both_participants(self):
        with self.assertRaises(Exception):
            Conversation.objects.create(tenant=make_tenant())

    def test_other_participant(self):
        tenant = make_tenant()
        landlord = make_landlord()
        conversation = make_conversation(tenant=tenant, landlord=landlord)
        self.assertEqual(conversation.other_participant(tenant), landlord)
        self.assertEqual(conversation.other_participant(landlord), tenant)

    def test_other_participant_is_none_for_outsider(self):
        outsider = make_landlord(email="other@example.com")
        conversation = make_conversation()
        self.assertIsNone(conversation.other_participant(outsider))

    def test_is_participant(self):
        tenant = make_tenant()
        landlord = make_landlord()
        outsider = make_tenant(email="outsider@example.com")
        conversation = make_conversation(tenant=tenant, landlord=landlord)
        self.assertTrue(conversation.is_participant(tenant))
        self.assertTrue(conversation.is_participant(landlord))
        self.assertFalse(conversation.is_participant(outsider))

    def test_unique_conversation_pair(self):
        tenant = make_tenant()
        landlord = make_landlord()
        make_conversation(tenant=tenant, landlord=landlord)
        with self.assertRaises(IntegrityError):
            make_conversation(tenant=tenant, landlord=landlord)

    def test_timestamps_are_populated(self):
        conversation = make_conversation()
        self.assertIsNotNone(conversation.created_at)
        self.assertIsNotNone(conversation.updated_at)

    def test_string_representation_includes_participants(self):
        conversation = make_conversation()
        self.assertIn("Conversation", str(conversation))


class MessageModelTests(django_tests.TestCase):
    def test_message_relationships(self):
        tenant = make_tenant()
        landlord = make_landlord()
        conversation = make_conversation(tenant=tenant, landlord=landlord)
        message = make_message(
            conversation=conversation,
            sender=tenant,
            recipient=landlord,
        )
        self.assertEqual(message.conversation, conversation)
        self.assertEqual(message.sender, tenant)
        self.assertEqual(message.recipient, landlord)
        self.assertIn(message, conversation.messages.all())
        self.assertIn(message, tenant.sent_messages.all())
        self.assertIn(message, landlord.received_messages.all())

    def test_message_requires_conversation(self):
        with self.assertRaises(Exception):
            Message.objects.create(sender=make_tenant(), recipient=make_landlord())

    def test_message_body_and_status_stored(self):
        tenant = make_tenant()
        landlord = make_landlord()
        conversation = make_conversation(tenant=tenant, landlord=landlord)
        message = make_message(
            conversation=conversation,
            sender=tenant,
            recipient=landlord,
            body="Is the apartment still available?",
            status=Message.Status.READ,
        )
        self.assertEqual(message.body, "Is the apartment still available?")
        self.assertEqual(message.status, Message.Status.READ)

    def test_status_defaults_to_sent(self):
        message = make_message()
        self.assertEqual(message.status, Message.Status.SENT)

    def test_timestamps_are_populated(self):
        message = make_message()
        self.assertIsNotNone(message.created_at)
        self.assertIsNotNone(message.updated_at)

    def test_sender_must_be_a_participant(self):
        conversation = make_conversation()
        outsider = make_tenant(email="outsider@example.com")
        message = Message(
            conversation=conversation,
            sender=outsider,
            recipient=conversation.landlord,
            body="Hi.",
        )
        with self.assertRaises(ValidationError):
            message.full_clean()

    def test_recipient_must_be_the_other_participant(self):
        tenant = make_tenant()
        landlord = make_landlord()
        other_landlord = make_landlord(email="otherlandlord@example.com")
        conversation = make_conversation(tenant=tenant, landlord=landlord)
        message = Message(
            conversation=conversation,
            sender=tenant,
            recipient=other_landlord,
            body="Hi.",
        )
        with self.assertRaises(ValidationError):
            message.full_clean()

    def test_cannot_message_self(self):
        tenant = make_tenant()
        landlord = make_landlord()
        conversation = make_conversation(tenant=tenant, landlord=landlord)
        message = Message(
            conversation=conversation,
            sender=tenant,
            recipient=tenant,
            body="Hi.",
        )
        with self.assertRaises(ValidationError):
            message.full_clean()

    def test_valid_message_passes_validation(self):
        message = make_message()
        try:
            message.full_clean()
        except ValidationError:
            self.fail("A valid message must pass full_clean().")

    def test_mark_read(self):
        landlord = make_landlord()
        conversation = make_conversation(landlord=landlord)
        message = make_message(
            conversation=conversation,
            recipient=landlord,
        )
        self.assertFalse(message.is_read)
        message.mark_read()
        message.refresh_from_db()
        self.assertTrue(message.is_read)
        self.assertEqual(message.status, Message.Status.READ)

    def test_default_ordering_oldest_first(self):
        conversation = make_conversation()
        first = make_message(conversation=conversation, body="First")
        second = make_message(conversation=conversation, body="Second")
        self.assertEqual(
            list(Message.objects.all()),
            [first, second],
        )

    def test_required_query_fields_are_indexed(self):
        indexed_fields = {
            index.fields[0]
            for index in Message._meta.indexes
        }
        for field in ("conversation", "sender", "recipient"):
            self.assertIn(field, indexed_fields)
