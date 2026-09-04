"""
Base Django settings for the Landlord-Tenant Direct Connect Platform.

This module contains settings shared by all environments (development and
production). Environment-specific settings live in ``development.py`` and
``production.py``.

Secrets (SECRET_KEY, database credentials) are loaded ONLY from environment
variables. They are never hard-coded in this file or committed to Git.
"""
import os
from datetime import timedelta
from pathlib import Path

from django.core.management.utils import get_random_secret_key

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------------
# Environment helper
# ---------------------------------------------------------------------------


def env(key, default=None):
    """Read an environment variable, returning ``default`` when unset."""
    return os.environ.get(key, default)


# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
# In production this MUST be supplied via the environment (see production.py).
SECRET_KEY = env("SECRET_KEY", get_random_secret_key())

DEBUG = False

ALLOWED_HOSTS = []

# ---------------------------------------------------------------------------
# Application definition
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    # Django default apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "drf_spectacular",
    "cloudinary_storage",
    # Project apps
      "apps.core",
      "apps.accounts",
      "apps.verification",
      "apps.apartments",
      "apps.recommendations",
      "apps.messaging",
      "apps.admin_dashboard",
      "apps.audit",
  ]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---------------------------------------------------------------------------
# Database (PostgreSQL)
# ---------------------------------------------------------------------------
# Configuration is driven by environment variables. No password or secret is
# hard-coded here. Sprint 1.4 will finalise the live connection and migrations.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DATABASE_NAME", "landlord_tenant_db"),
        "USER": env("DATABASE_USER", ""),
        "PASSWORD": env("DATABASE_PASSWORD", ""),
        "HOST": env("DATABASE_HOST", "127.0.0.1"),
        "PORT": env("DATABASE_PORT", "5432"),
    }
}

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Custom user model (apps.accounts)
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"

# Session-based presentation authentication (AGENTS 19). Pages that require a
# login redirect here; successful logins land on the role dashboard.
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation."
        "UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static files, media
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Consistent error envelope across the whole API (Sprint 6.4).
    "EXCEPTION_HANDLER": "apps.core.api.api_exception_handler",
    # Scoped rate limiting for the public authentication endpoints, which are
    # the natural brute-force targets. Other endpoints are not globally limited
    # so legitimate multi-request flows are unaffected (AGENTS 27, §24).
    "DEFAULT_THROTTLE_RATES": {
        "auth": "60/min",
    },
}

# JWT lives a short time for access; the refresh token can be exchanged for a
# new access token. On logout the refresh token is revoked via the blacklist.
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Landlord-Tenant Direct Connect Platform API",
    "DESCRIPTION": (
        "API for a landlord-to-tenant contact platform with Weighted KNN "
        "apartment recommendations."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ---------------------------------------------------------------------------
# Email (Django 6.1 uses the MAILERS setting)
# Development default prints to console; production overrides the backend.
# ---------------------------------------------------------------------------
MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}

# ---------------------------------------------------------------------------
# Logging (Phase 6, Sprint 6.5 - Audit, Logging and Data Integrity)
# ---------------------------------------------------------------------------
# Application-wide logging configuration. The root logger captures actionable
# INFO messages to the console. An `apps.audit` logger exists so audit-event
# emissions can be filtered/tuned independently. Production overrides the
# handler configuration (see production.py) but reuses this structure.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": (
                "{levelname} {asctime} {name} {module} "
                "{process:d} {thread:d} {message}"
            ),
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {asctime} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "apps.audit": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
