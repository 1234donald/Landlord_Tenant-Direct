from django.contrib import admin

from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    """Admin configuration for audit events.

    Audit events are append-only and read-only in the admin interface.
    """

    list_display = [
        "id",
        "category",
        "action",
        "user",
        "target_content_type",
        "target_object_id",
        "ip_address",
        "created_at",
    ]
    list_filter = ["category", "created_at"]
    search_fields = ["action", "user__email", "target_content_type"]
    readonly_fields = [
        "user",
        "category",
        "action",
        "target_content_type",
        "target_object_id",
        "ip_address",
        "extra",
        "created_at",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
