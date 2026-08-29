"""
Development settings for the Landlord-Tenant Direct Connect Platform.

Used for local development. The ``.env`` file (loaded in the settings package
``__init__.py`` before any settings module is imported) supplies local secrets
and host configuration.
"""
import os

from .base import *  # noqa: F401,F403
from .base import env

# ---------------------------------------------------------------------------
# Development overrides
# ---------------------------------------------------------------------------
DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# A strong random SECRET_KEY is generated at startup unless one is provided.
# Keep the value from `.env` stable between restarts for session persistence.
SECRET_KEY = env("SECRET_KEY", SECRET_KEY)

# ---------------------------------------------------------------------------
# Database defaults for development
# ---------------------------------------------------------------------------
DATABASES["default"]["HOST"] = env("DATABASE_HOST", "127.0.0.1")  # noqa: F405
DATABASES["default"]["PORT"] = env("DATABASE_PORT", "5432")  # noqa: F405

# Email backend for development: print to console instead of sending.
MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}

# ---------------------------------------------------------------------------
# Namespaced cache / sessions for local use (defaults are fine for dev).
# ---------------------------------------------------------------------------
