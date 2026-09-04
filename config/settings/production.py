"""
Production settings for the Landlord-Tenant Direct Connect Platform.

Used in deployed environments. Security protections are enabled by default
and MUST NOT be disabled to make the application run.

Configured via environment variables: DEBUG=False, a strong SECRET_KEY,
ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS and PostgreSQL credentials.
"""
import os
import urllib.parse

from .base import *  # noqa: F401,F403
from .base import env

# ---------------------------------------------------------------------------
# Production overrides
# ---------------------------------------------------------------------------
DEBUG = env("DEBUG", "False").lower() in ("1", "true", "yes", "on")

SECRET_KEY = env("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY must be set via the environment in production. "
        "Never run production without a strong, private SECRET_KEY."
    )

ALLOWED_HOSTS = [
    host.strip()
    for host in env("ALLOWED_HOSTS", "").split(",")
    if host.strip()
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in env("CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]

# ---------------------------------------------------------------------------
# Security hardening (production)
# ---------------------------------------------------------------------------
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ---------------------------------------------------------------------------
# Production static file serving via WhiteNoise
# ---------------------------------------------------------------------------
MIDDLEWARE.insert(0, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa: F405

# Media storage: use Cloudinary when CLOUDINARY_URL is provided (Render,
# production), otherwise fall back to local file system (self-hosted).
_media_backend = "django.core.files.storage.FileSystemStorage"
if env("CLOUDINARY_URL"):
    _media_backend = "cloudinary_storage.storage.CloudinaryMediaStorage"

STORAGES = {
    "default": {
        "BACKEND": _media_backend,
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ---------------------------------------------------------------------------
# Production database
# ---------------------------------------------------------------------------
# Render (and similar platforms) supply a single DATABASE_URL environment
# variable.  When it is present we parse it and use it; otherwise we fall back
# to the individual DATABASE_* variables already inherited from base.py.
# This preserves full local development compatibility without requiring any
# new third-party dependency.
DATABASE_URL = env("DATABASE_URL")
if DATABASE_URL:
    url = urllib.parse.urlparse(DATABASE_URL)
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": url.path[1:],          # strip leading "/"
        "USER": url.username or "",
        "PASSWORD": url.password or "",
        "HOST": url.hostname or "",
        "PORT": url.port or "5432",
    }
else:
    DATABASES["default"]["HOST"] = env("DATABASE_HOST", "")  # noqa: F405
    DATABASES["default"]["PORT"] = env("DATABASE_PORT", "5432")  # noqa: F405
    DATABASES["default"]["USER"] = env("DATABASE_USER", "")  # noqa: F405
    DATABASES["default"]["PASSWORD"] = env("DATABASE_PASSWORD", "")  # noqa: F405

# ---------------------------------------------------------------------------
# Production email (Django 6.1 MAILERS)
# Production MUST use a production-ready backend (SMTP by default); it never
# inherits the development console backend from base.py, so deployment checks
# no longer report mail.E001 (AGENTS 19, 20, 44). All credentials come from
# the environment and are never hard-coded. No email feature is currently
# shipped, so these settings only make the configuration production-safe.
# ---------------------------------------------------------------------------
MAILERS = {
    "default": {
        "BACKEND": env(
            "EMAIL_BACKEND",
            "django.core.mail.backends.smtp.EmailBackend",
        ),
        "OPTIONS": {
            "host": env("EMAIL_HOST", "localhost"),
            "port": int(env("EMAIL_PORT", "587") or "587"),
            "username": env("EMAIL_HOST_USER", ""),
            "password": env("EMAIL_HOST_PASSWORD", ""),
            "use_tls": env("EMAIL_USE_TLS", "True").lower()
            in ("1", "true", "yes", "on"),
        },
    },
}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
