from django.contrib import admin

from .models import Preference, Recommendation, RecommendationItem


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


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    """Admin configuration for persisted recommendation runs."""

    list_display = ["id", "tenant", "preference", "algorithm", "k", "created_at"]
    list_filter = ["algorithm"]
    search_fields = ["tenant__email"]
    readonly_fields = ["created_at"]
    fieldsets = (
        (None, {"fields": ("tenant", "preference", "algorithm", "k")}),
        ("Timestamps", {"fields": ("created_at",)}),
    )


class RecommendationItemInline(admin.TabularInline):
    model = RecommendationItem
    extra = 0
    readonly_fields = ["apartment", "rank", "distance", "similarity"]


@admin.register(RecommendationItem)
class RecommendationItemAdmin(admin.ModelAdmin):
    """Admin configuration for ranked recommendation items."""

    list_display = ["id", "recommendation", "apartment", "rank", "distance", "similarity"]
    list_filter = ["rank"]
    search_fields = ["apartment__title"]
    readonly_fields = ["recommendation", "apartment", "rank", "distance", "similarity"]
