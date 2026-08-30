"""Views for the Messaging module (Phase 4, Sprint 4.5).

Implements the Messaging API (§24.5):
- ``GET  /api/v1/messages/``                         list the user's messages
- ``POST /api/v1/messages/``                         send a message
- ``GET  /api/v1/messages/{id}/``                    retrieve a single message
- ``GET  /api/v1/conversations/``                    list the user's conversations
- ``GET  /api/v1/conversations/{id}/``               retrieve a conversation + history
- ``POST /api/v1/conversations/{id}/messages/``      send within a conversation

Role enforcement: messages and conversations are private to the two
participants (a TENANT and a LANDLORD) or an administrator. A user can only see
conversations they belong to and messages they sent or received, and can only
send a message to the other participant of a conversation they are part of.
Retrieving a message/conversation marks the user's incoming messages as read so
the message status reflects delivery (``SENT``) and receipt (``READ``).
"""
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Conversation, Message
from .permissions import (
    IsConversationParticipantOrAdmin,
    IsParticipantForMessage,
)
from .serializers import (
    ConversationMessageCreateSerializer,
    ConversationSerializer,
    ConversationSummarySerializer,
    MessageCreateSerializer,
    MessageSerializer,
    validate_conversation_pair,
)

User = get_user_model()


class MessageListCreateView(APIView):
    """List the authenticated user's messages or send a new message.

    ``GET`` returns messages the user sent or received. ``POST`` sends a
    message to a recipient, creating (or reusing) the tenant-landlord
    conversation between them. An administrator sees all messages (AGENTS 8).
    """

    def get(self, request):
        if request.user.is_admin:
            queryset = Message.objects.all()
        else:
            queryset = Message.objects.filter(
                sender=request.user,
            ) | Message.objects.filter(recipient=request.user)
        queryset = queryset.select_related(
            "conversation", "sender", "recipient"
        ).order_by("-created_at", "-id")
        serializer = MessageSerializer(queryset, many=True)
        return Response(
            {
                "success": True,
                "message": "Messages retrieved.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        serializer = MessageCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Sending the message failed.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        message = serializer.save()
        return Response(
            {
                "success": True,
                "message": "Message sent.",
                "data": MessageSerializer(message).data,
            },
            status=status.HTTP_201_CREATED,
        )


class MessageDetailView(APIView):
    """Retrieve a single message.

    Access is restricted to the message's sender or recipient, or an
    administrator. Retrieving marks the message as read when the recipient is
    the current user.
    """

    permission_classes = [IsParticipantForMessage]

    def _get_owned_message(self, request, pk):
        message = get_object_or_404(Message, pk=pk)
        self.check_object_permissions(request, message)
        return message

    def get(self, request, pk):
        message = self._get_owned_message(request, pk)
        if (
            not message.is_read
            and message.recipient_id == request.user.id
        ):
            message.mark_read()
        serializer = MessageSerializer(message)
        return Response(
            {
                "success": True,
                "message": "Message retrieved.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class ConversationListCreateView(APIView):
    """List the authenticated user's conversations or start a new one.

    ``GET`` returns conversations where the user is a participant. ``POST``
    creates a new tenant-landlord conversation between the authenticated user
    and the supplied counterpart. An administrator sees all conversations
    (AGENTS 8).
    """

    def get(self, request):
        if request.user.is_admin:
            queryset = Conversation.objects.all()
        else:
            queryset = Conversation.objects.filter(
                tenant=request.user,
            ) | Conversation.objects.filter(landlord=request.user)
        queryset = queryset.prefetch_related("messages").order_by("-updated_at")
        serializer = ConversationSummarySerializer(queryset, many=True)
        return Response(
            {
                "success": True,
                "message": "Conversations retrieved.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        counterpart_id = request.data.get("counterpart")
        if counterpart_id is None:
            return Response(
                {
                    "success": False,
                    "message": "Conversation creation failed.",
                    "errors": {"counterpart": "A counterpart user id is required."},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        peer = get_object_or_404(
            User,
            pk=counterpart_id,
            is_active=True,
        )
        if request.user.is_tenant and peer.is_landlord:
            tenant, landlord = request.user, peer
        elif request.user.is_landlord and peer.is_tenant:
            tenant, landlord = peer, request.user
        else:
            return Response(
                {
                    "success": False,
                    "message": "Conversation creation failed.",
                    "errors": {
                        "counterpart": (
                            "A conversation can only be created between a "
                            "tenant and a landlord."
                        )
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        validate_conversation_pair(tenant, landlord)
        conversation, _ = Conversation.objects.get_or_create(
            tenant=tenant,
            landlord=landlord,
        )
        return Response(
            {
                "success": True,
                "message": "Conversation retrieved or created.",
                "data": ConversationSerializer(conversation).data,
            },
            status=status.HTTP_200_OK,
        )


class ConversationDetailView(APIView):
    """Retrieve a conversation and its message history.

    Access is restricted to a conversation's participants or an administrator.
    Retrieving marks the current user's incoming messages in the conversation
    as read.
    """

    permission_classes = [IsConversationParticipantOrAdmin]

    def get(self, request, pk):
        conversation = get_object_or_404(Conversation, pk=pk)
        self.check_object_permissions(request, conversation)
        conc_messages = conversation.messages.filter(
            recipient=request.user,
            status=Message.Status.SENT,
        )
        for message in conc_messages:
            message.mark_read()
        serializer = ConversationSerializer(conversation)
        return Response(
            {
                "success": True,
                "message": "Conversation retrieved.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class ConversationMessageCreateView(APIView):
    """Send a message within an existing conversation.

    Access is restricted to a conversation's participants or an administrator.
    The sender is the authenticated participant and the recipient is the other
    participant, both derived from the conversation.
    """

    permission_classes = [IsConversationParticipantOrAdmin]

    def post(self, request, pk):
        conversation = get_object_or_404(Conversation, pk=pk)
        self.check_object_permissions(request, conversation)
        serializer = ConversationMessageCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Sending the message failed.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        recipient = conversation.other_participant(request.user)
        if recipient is None:
            return Response(
                {
                    "success": False,
                    "message": "Sending the message failed.",
                    "errors": {"detail": "You are not a participant of this conversation."},
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            recipient=recipient,
            body=serializer.validated_data["body"],
        )
        return Response(
            {
                "success": True,
                "message": "Message sent.",
                "data": MessageSerializer(message).data,
            },
            status=status.HTTP_201_CREATED,
        )
