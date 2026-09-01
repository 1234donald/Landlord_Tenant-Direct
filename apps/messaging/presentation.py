"""HTML presentation views for the Messaging module (direct tenant-landlord).

These server-rendered pages let a TENANT and a LANDLORD communicate through the
``Conversation`` / ``Message`` models (AGENTS 8): a role-aware inbox and a
conversation thread page. A user can only ever see conversations they belong to
and messages they sent or received, mirroring the API permission rules. Opening
a thread marks the user's incoming messages as read.

Views:
- ``ConversationListView``  - the authenticated user's inbox (role-aware);
- ``ConversationDetailView``- a single thread plus a send form;
- ``NewConversationView``   - a tenant starts (or resumes) a thread with a
  landlord.
"""
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.accounts.presentation import RoleRequiredMixin

from .models import Conversation, Message

User = get_user_model()


class ConversationListView(LoginRequiredMixin, RoleRequiredMixin, View):
    """Role-aware inbox listing the authenticated user's conversations.

    Tenants see conversations they participate in as tenants; landlords see
    theirs as landlords. The page only ever shows the current user's own
    conversations, so a user never sees another role's data (AGENTS 8).
    """

    template_name = "messaging/conversation_list.html"
    allowed_roles = ("tenant", "landlord")

    def get(self, request):
        user = request.user
        if user.is_tenant:
            conversations = user.tenant_conversations.select_related(
                "landlord"
            ).prefetch_related("messages")
        else:
            conversations = user.landlord_conversations.select_related(
                "tenant"
            ).prefetch_related("messages")
        return render(
            request,
            self.template_name,
            {"conversations": conversations},
        )


class ConversationDetailView(LoginRequiredMixin, RoleRequiredMixin, View):
    """A single conversation thread with a send-message form.

    Only a participant of the conversation can view it (AGENTS 8). Opening the
    thread marks the viewer's incoming messages as read.
    """

    template_name = "messaging/conversation_detail.html"
    allowed_roles = ("tenant", "landlord")

    def get_conversation(self, request, pk):
        conversation = get_object_or_404(Conversation, pk=pk)
        if not conversation.is_participant(request.user):
            return None
        return conversation

    def get(self, request, pk):
        conversation = self.get_conversation(request, pk)
        if conversation is None:
            return HttpResponseForbidden("Forbidden")
        self._mark_read(conversation, request.user)
        messages_qs = conversation.messages.select_related("sender").all()
        return render(
            request,
            self.template_name,
            {
                "conversation": conversation,
                "thread": messages_qs,
                "other": conversation.other_participant(request.user),
            },
        )

    def post(self, request, pk):
        conversation = self.get_conversation(request, pk)
        if conversation is None:
            return HttpResponseForbidden("Forbidden")
        body = (request.POST.get("body") or "").strip()
        other = conversation.other_participant(request.user)
        if body and other is not None:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                recipient=other,
                body=body,
            )
        return redirect("conversation-detail", pk=conversation.pk)

    @staticmethod
    def _mark_read(conversation, user):
        Message.objects.filter(
            conversation=conversation, recipient=user, status=Message.Status.SENT
        ).update(status=Message.Status.READ)


class NewConversationView(LoginRequiredMixin, RoleRequiredMixin, View):
    """Tenant starts (or resumes) a conversation with a landlord.

    The tenant selects a landlord (from the apartment they are interested in) to
    begin a thread. If a conversation already exists between the pair it is
    reused (the model has a unique tenant-landlord constraint).
    """

    template_name = "messaging/new_conversation.html"
    allowed_roles = ("tenant",)

    def get(self, request):
        landlord_id = request.GET.get("landlord") or request.GET.get("landlord_id")
        entries = []
        preselected_id = None
        if landlord_id and str(landlord_id).isdigit():
            preselected_id = int(landlord_id)
        else:
            for landlord in (
                User.objects.filter(is_active=True, role=User.Role.LANDLORD)
                .filter(apartments__availability=True)
                .distinct()
            ):
                first_listing = (
                    landlord.apartments.filter(availability=True).first()
                )
                entries.append(
                    {
                        "id": landlord.id,
                        "full_name": landlord.get_full_name() or landlord.email,
                        "email": landlord.email,
                        "location": (
                            first_listing.location if first_listing else "Location on request"
                        ),
                    }
                )
        return render(
            request,
            self.template_name,
            {"landlord_entries": entries, "preselected_id": preselected_id},
        )

    def post(self, request):
        landlord_id = request.POST.get("landlord")
        if not landlord_id or not str(landlord_id).isdigit():
            messages.error(request, "Please choose a landlord to contact.")
            return redirect("new-conversation")
        landlord = get_object_or_404(User, pk=int(landlord_id), role=User.Role.LANDLORD)
        conversation, _ = Conversation.objects.get_or_create(
            tenant=request.user, landlord=landlord
        )
        return redirect("conversation-detail", pk=conversation.pk)
