from django.contrib import admin

from .models import VerificationRequest


@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    """Admin configuration for landlord verification requests."""

    list_display = [
        "id",
        "landlord",
        "status",
        "submitted_at",
        "reviewed_by",
        "reviewed_at",
    ]
    list_filter = ["status", "submitted_at"]
    search_fields = ["landlord__email", "landlord__full_name", "remarks"]
    readonly_fields = ["submitted_at", "reviewed_at", "updated_at"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "landlord",
                    "information",
                    "status",
                    "remarks",
                )
            },
        ),
        ("Review", {"fields": ("reviewed_by", "reviewed_at")}),
        ("Timestamps", {"fields": ("submitted_at", "updated_at")}),
    )
