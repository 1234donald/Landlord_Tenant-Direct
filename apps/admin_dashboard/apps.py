from django.apps import AppConfig


class AdminDashboardConfig(AppConfig):
    """Application configuration for the administrator dashboard module."""

    name = "apps.admin_dashboard"
    verbose_name = "Administrator Dashboard"
    default_auto_field = "django.db.models.BigAutoField"
