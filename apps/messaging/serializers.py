"""Serializers for the Messaging module (Phase 4, Sprint 4.5).

These support direct tenant-landlord messaging (§17): sending and receiving
messages, conversation history and message status. Senders and recipients are
always derived from the authenticated request and the conversation participants;
they are never freely client-supplied in a way that breaks the two-participant
model (AGENTS 8, 23).
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Conversation, Message

User = get_user_model()


class _ConversationMembershipValidator:
    """Validate that a candidate participant pairing forms a valid thread.

    A conversation is only valid between one TENANT and one LANDLORD, and the
    two participants must be distinct users.
    """

    def __call__(self, tenant, landlord):
        if tenant is None or landlord is None:
            raise serializers.ValidationError(
                "A conversation requires both a tenant and a landlord."
            )
        if tenant.id == landlord.id:
            raise serializers.ValidationError(
                "The two conversation participants must be different users."
            )
        if not tenant.is_tenant:
            raise serializers.ValidationError(
                "The tenant participant must have the tenant role."
            )
        if not landlord.is_landlord:
            raise serializers.ValidationError(
                "The landlord participant must have the landlord role."
            )


validate_conversation_pair = _ConversationMembershipValidator()


class ParticipantSerializer(serializers.ModelSerializer):
    """Compact read representation of a conversation participant."""

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "role"]
        read_only_fields = fields


class MessageSerializer(serializers.ModelSerializer):
    """Read representation of a single message."""

    sender_email = serializers.EmailField(source="sender.email", read_only=True)
    recipient_email = serializers.EmailField(
        source="recipient.email", read_only=True
    )

    class Meta:
        model = Message
        fields = [
            "id",
            "conversation",
            "sender",
            "sender_email",
            "recipient",
            "recipient_email",
            "body",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ConversationSerializer(serializers.ModelSerializer):
    """Read representation of a conversation with its message history."""

    tenant_detail = ParticipantSerializer(source="tenant", read_only=True)
    landlord_detail = ParticipantSerializer(source="landlord", read_only=True)
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = [
            "id",
            "tenant",
            "tenant_detail",
            "landlord",
            "landlord_detail",
            "messages",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ConversationSummarySerializer(serializers.ModelSerializer):
    """Compact read representation of a conversation (without full history)."""

    tenant_detail = ParticipantSerializer(source="tenant", read_only=True)
    landlord_detail = ParticipantSerializer(source="landlord", read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id",
            "tenant",
            "tenant_detail",
            "landlord",
            "landlord_detail",
            "last_message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_last_message(self, obj):
        message = obj.messages.last()
        if message is None:
            return None
        return MessageSerializer(message).data


class MessageCreateSerializer(serializers.Serializer):
    """Create a message between the authenticated user and a recipient.

    Used by ``POST /api/v1/messages/``. The recipient is supplied; the sender is
    always the authenticated request user. The message is attached to the
    (found-or-created) conversation between the two users, which must be a
    valid TENANT-LANDLORD pairing.
    """

    recipient = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        help_text="The id of the user to message.",
    )
    body = serializers.CharField()

    def validate_recipient(self, value):
        if value.id == self.context["request"].user.id:
            raise serializers.ValidationError(
                "You cannot send a message to yourself."
            )
        return value

    def validate_body(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(
                "The message body cannot be empty."
            )
        if len(value) > 5000:
            raise serializers.ValidationError(
                "A message must be 5000 characters or fewer."
            )
        return value

    def validate(self, attrs):
        sender = self.context["request"].user
        recipient = attrs["recipient"]
        if sender.is_tenant and recipient.is_landlord:
            tenant, landlord = sender, recipient
        elif sender.is_landlord and recipient.is_tenant:
            tenant, landlord = recipient, sender
        else:
            raise serializers.ValidationError(
                "Messages can only be exchanged between a tenant and a landlord."
            )
        validate_conversation_pair(tenant, landlord)
        conversation, _ = Conversation.objects.get_or_create(
            tenant=tenant,
            landlord=landlord,
        )
        attrs["conversation"] = conversation
        attrs["sender"] = sender
        attrs["recipient"] = recipient
        return attrs

    def create(self, validated_data):
        return Message.objects.create(
            conversation=validated_data["conversation"],
            sender=validated_data["sender"],
            recipient=validated_data["recipient"],
            body=validated_data["body"],
        )


class ConversationMessageCreateSerializer(serializers.Serializer):
    """Create a message within an existing conversation.

    Used by ``POST /api/v1/conversations/{id}/messages/``. The sender is the
    authenticated participant and the recipient is the other participant; both
    are derived from the conversation.
    """

    body = serializers.CharField()

    def validate_body(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(
                "The message body cannot be empty."
            )
        if len(value) > 5000:
            raise serializers.ValidationError(
                "A message must be 5000 characters or fewer."
            )
        return value
