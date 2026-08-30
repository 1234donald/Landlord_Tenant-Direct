from django.contrib import admin

from .models import Apartment


@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    """Admin configuration for apartment listings."""

    list_display = [
        "id",
        "title",
        "landlord",
        "location",
        "rental_price",
        "apartment_type",
        "bedrooms",
        "bathrooms",
        "availability",
        "created_at",
    ]
    list_filter = ["availability", "apartment_type", "location"]
    search_fields = ["title", "location", "address", "landlord__email"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "landlord",
                    "title",
                    "description",
                    "location",
                    "address",
                )
            },
        ),
        (
            "Pricing and Size",
            {
                "fields": (
                    "rental_price",
                    "apartment_type",
                    "bedrooms",
                    "bathrooms",
                )
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
        ("Availability", {"fields": ("availability",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
