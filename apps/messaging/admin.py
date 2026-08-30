from django.contrib import admin

from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    """Inline listing of messages within a conversation."""

    model = Message
    extra = 0
    readonly_fields = ["sender", "recipient", "body", "status", "created_at"]

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """Admin configuration for tenant-landlord conversations."""

    list_display = ["id", "tenant", "landlord", "created_at", "updated_at"]
    list_filter = ["created_at"]
    search_fields = [
        "tenant__email",
        "tenant__full_name",
        "landlord__email",
        "landlord__full_name",
    ]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin configuration for messages."""

    list_display = [
        "id",
        "conversation",
        "sender",
        "recipient",
        "status",
        "created_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["sender__email", "recipient__email", "body"]
    readonly_fields = ["conversation", "sender", "recipient", "created_at", "updated_at"]
