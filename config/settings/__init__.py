"""
Settings package for the Landlord-Tenant Direct Connect Platform.

Loading order:
1. Load ``.env`` (local secrets) before any settings module is imported.
2. Default to the ``development`` settings so ``config.settings`` works
   out of the box locally. Production sets ``DJANGO_SETTINGS_MODULE`` to
   ``config.settings.production``.
"""
from pathlib import Path

from dotenv import load_dotenv

# Load local environment variables from the repository-root .env file.
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

# Default settings for local development.
from .development import *  # noqa: E402,F401,F403
