from django.contrib import admin

from .models import Preference


@admin.register(Preference)
class PreferenceAdmin(admin.ModelAdmin):
    """Admin configuration for tenant preferences."""

    list_display = [
        "id",
        "tenant",
        "location",
        "max_rent",
        "apartment_type",
        "bedrooms",
        "bathrooms",
        "created_at",
    ]
    list_filter = ["apartment_type", "furnished", "parking"]
    search_fields = ["tenant__email", "location"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        (
            None,
            {
                "fields": ("tenant", "location"),
            },
        ),
        (
            "Pricing and Size",
            {
                "fields": ("max_rent", "apartment_type", "bedrooms", "bathrooms"),
            },
        ),
        (
            "Facilities",
            {
                "fields": (
                    "parking",
                    "electricity",
                    "water",
                    "security",
                    "furnished",
                    "additional_facilities",
                )
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
