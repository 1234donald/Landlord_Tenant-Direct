"""Messaging data model (Phase 4, Sprint 4.5).

The ``Conversation`` and ``Message`` models implement direct tenant-landlord
communication (§17). A conversation links exactly one TENANT and one LANDLORD,
and a message records the sender, the recipient, the message body, its delivery
status and a timestamp. Only HTTP-based messaging is supported in V1; no
WebSocket infrastructure is added (§17, TECH_STACK_AND_IMPLEMENTATION_PLAN §I).
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Conversation(models.Model):
    """A direct communication thread between one tenant and one landlord.

    Relationships:
        - ``tenant`` (required): the TENANT participant.
        - ``landlord`` (required): the LANDLORD participant.
    """

    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tenant_conversations",
        limit_choices_to={"role": "TENANT"},
        help_text="The tenant participant in this conversation.",
    )
    landlord = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="landlord_conversations",
        limit_choices_to={"role": "LANDLORD"},
        help_text="The landlord participant in this conversation.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "landlord"],
                name="unique_conversation_pair",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant"]),
            models.Index(fields=["landlord"]),
        ]

    def __str__(self):
        return f"Conversation {self.pk} ({self.tenant_id}, {self.landlord_id})"

    def other_participant(self, user):
        """Return the other conversation participant relative to ``user``.

        Returns ``None`` when the user is not a participant of the
        conversation.
        """
        if user.id == self.tenant_id:
            return self.landlord
        if user.id == self.landlord_id:
            return self.tenant
        return None

    def is_participant(self, user):
        """Return whether ``user`` is one of the two conversation participants."""
        return bool(
            user
            and user.id in (self.tenant_id, self.landlord_id)
        )


class Message(models.Model):
    """A single message within a conversation.

    Relationships:
        - ``conversation`` (required): the conversation the message belongs to.
        - ``sender`` (required): the user who sent the message.
        - ``recipient`` (required): the intended recipient of the message.
    """

    class Status(models.TextChoices):
        SENT = "SENT", "Sent"
        READ = "READ", "Read"

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
        help_text="The conversation this message belongs to.",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages",
        help_text="The user who sent the message.",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_messages",
        help_text="The intended recipient of the message.",
    )
    body = models.TextField(
        help_text="The content of the message.",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SENT,
        help_text="Delivery/read status of the message.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at", "id"]
        indexes = [
            models.Index(fields=["conversation"]),
            models.Index(fields=["sender"]),
            models.Index(fields=["recipient"]),
        ]

    def __str__(self):
        return f"Message {self.pk} in conversation {self.conversation_id}"

    def clean(self):
        """Validate a message before saving.

        The body must not be blank (AGENTS 23) and the sender and recipient
        must be the two distinct participants of the conversation (a user can
        only message the other participant, not themselves).
        """
        super().clean()
        errors = {}

        if self.sender_id is not None and self.recipient_id is not None:
            if self.sender_id == self.recipient_id:
                errors["recipient"] = "You cannot send a message to yourself."

        if self.conversation_id is not None and self.sender_id is not None:
            if not self.conversation.is_participant(self.sender):
                errors["sender"] = "The sender is not a participant of this conversation."
            else:
                other = self.conversation.other_participant(self.sender)
                if other is not None and self.recipient_id != other.id:
                    errors["recipient"] = (
                        "The recipient must be the other participant of the "
                        "conversation."
                    )

        if errors:
            raise ValidationError(errors)

    def mark_read(self):
        """Mark this message as read by its recipient."""
        if self.status != self.Status.READ:
            self.status = self.Status.READ
            self.save(update_fields=["status", "updated_at"])

    @property
    def is_read(self):
        return self.status == self.Status.READ
