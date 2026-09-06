"""
Tests for the ``create_admin`` management command (deployment helper).

Verifies that the command is idempotent and only creates an administrator
account when ADMIN_EMAIL/ADMIN_PASSWORD are provided via the environment.
"""
import os
from unittest import mock

import django.test as django_tests
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError

User = get_user_model()


def run_with_env(env, *args):
    with mock.patch.dict(os.environ, env, clear=False):
        call_command("create_admin", *args)


class CreateAdminCommandTests(django_tests.TestCase):
    def test_no_admin_email_is_a_noop(self):
        run_with_env({})
        self.assertEqual(User.objects.all().count(), 0)

    def test_creates_administrator_account(self):
        run_with_env(
            {
                "ADMIN_EMAIL": "admin@example.com",
                "ADMIN_PASSWORD": "StrongPass123!",
                "ADMIN_FULL_NAME": "System Admin",
            }
        )
        admin = User.objects.get(email="admin@example.com")
        self.assertEqual(admin.role, User.Role.ADMIN)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertEqual(admin.full_name, "System Admin")
        self.assertTrue(admin.check_password("StrongPass123!"))

    def test_is_idempotent_when_admin_exists(self):
        run_with_env(
            {
                "ADMIN_EMAIL": "admin@example.com",
                "ADMIN_PASSWORD": "StrongPass123!",
            }
        )
        first_id = User.objects.get(email="admin@example.com").id
        run_with_env(
            {
                "ADMIN_EMAIL": "admin@example.com",
                "ADMIN_PASSWORD": "DifferentPass123!",
            }
        )
        self.assertEqual(User.objects.filter(email="admin@example.com").count(), 1)
        same_admin = User.objects.get(email="admin@example.com")
        self.assertEqual(same_admin.id, first_id)
        # An existing password is preserved on subsequent runs.
        self.assertTrue(same_admin.check_password("StrongPass123!"))

    def test_requires_password_when_email_set(self):
        with mock.patch.dict(os.environ, {"ADMIN_EMAIL": "admin@example.com"}, clear=False):
            with self.assertRaises(CommandError):
                call_command("create_admin")