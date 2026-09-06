"""
Create or sync the platform administrator from environment variables.

Idempotent deployment helper. The administrator role is assigned explicitly
because ``createsuperuser`` would create an account with the default TENANT
role, which cannot access the administrator console (AGENTS 8).

Sourced from environment variables (never committed, AGENTS 19, 20):
- ``ADMIN_EMAIL``      (required to enable)
- ``ADMIN_PASSWORD``   (required when ``ADMIN_EMAIL`` is set; used only when
                       the account is first created)
- ``ADMIN_FULL_NAME``  (optional, defaults to "Platform Administrator")

When ``ADMIN_EMAIL`` is unset the command is a safe no-op so it can run on
every boot (e.g. inside a Render start command) without requiring input.
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Create or sync the platform administrator from ADMIN_EMAIL/"
        "ADMIN_PASSWORD environment variables (idempotent)."
    )

    def handle(self, *args, **options):
        email = os.environ.get("ADMIN_EMAIL", "").strip().lower()
        password = os.environ.get("ADMIN_PASSWORD", "")
        full_name = os.environ.get(
            "ADMIN_FULL_NAME", "Platform Administrator"
        ).strip() or "Platform Administrator"

        if not email:
            self.stdout.write(
                self.style.NOTICE(
                    "ADMIN_EMAIL not set; administrator creation skipped."
                )
            )
            return

        if not password:
            raise CommandError(
                "ADMIN_EMAIL is set but ADMIN_PASSWORD is empty. "
                "Provide ADMIN_PASSWORD via the environment."
            )

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "full_name": full_name,
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )

        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created administrator account for {email}."
                )
            )
            return

        changed = False
        if user.role != User.Role.ADMIN or not user.is_staff or not user.is_superuser:
            user.role = User.Role.ADMIN
            user.is_staff = True
            user.is_superuser = True
            user.save(update_fields=["role", "is_staff", "is_superuser"])
            changed = True

        if changed:
            self.stdout.write(
                self.style.SUCCESS(f"Promoted {email} to administrator.")
            )
        else:
            self.stdout.write(
                f"Administrator {email} already exists; no change."
            )