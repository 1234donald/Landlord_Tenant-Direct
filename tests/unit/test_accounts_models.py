"""
Unit tests for Phase 2, Sprint 2.1 - Custom User Model and Roles.

These verify the email-based custom User model, its three roles, the custom
user manager, and role helper properties. They require a test database.
"""
import django.test as django_tests
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


class UserManagerCreateTests(django_tests.TestCase):
    def test_create_user_creates_active_non_staff_user(self):
        user = User.objects.create_user(
            email="tenant@example.com",
            password="StrongPass123!",
            full_name="Tenant One",
        )
        self.assertEqual(user.email, "tenant@example.com")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.role, User.Role.TENANT)

    def test_create_user_normalises_email_domain(self):
        # Django's normalize_email lowercases only the domain portion; the
        # local part is preserved as provided (RFC 5321 allows case there).
        user = User.objects.create_user(
            email="Tenant@Example.COM",
            password="StrongPass123!",
            full_name="Tenant One",
        )
        self.assertEqual(user.email, "Tenant@example.com")

    def test_create_user_requires_email(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email="",
                password="StrongPass123!",
                full_name="No Email",
            )

    def test_create_user_hashes_password(self):
        user = User.objects.create_user(
            email="hash@example.com",
            password="PlainText-#123",
            full_name="Hash Test",
        )
        self.assertNotEqual(user.password, "PlainText-#123")
        self.assertTrue(user.password.startswith("pbkdf2_"))

    def test_create_superuser_sets_staff_and_superuser(self):
        admin = User.objects.create_superuser(
            email="admin@example.com",
            password="AdminPass123!",
            full_name="System Admin",
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_active)

    def test_create_superuser_requires_staff(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="bad@example.com",
                password="AdminPass123!",
                full_name="Bad Admin",
                is_staff=False,
            )

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(
            email="dup@example.com",
            password="StrongPass123!",
            full_name="First",
        )
        with self.assertRaises(Exception):
            User.objects.create_user(
                email="dup@example.com",
                password="StrongPass123!",
                full_name="Second",
            )


class UserRoleTests(django_tests.TestCase):
    def test_role_choices(self):
        self.assertEqual(
            set(User.Role.values),
            {User.Role.TENANT, User.Role.LANDLORD, User.Role.ADMIN},
        )

    def test_default_role_is_tenant(self):
        user = User.objects.create_user(
            email="default@example.com",
            password="StrongPass123!",
            full_name="Default Role",
        )
        self.assertEqual(user.role, User.Role.TENANT)

    def test_role_helper_properties(self):
        tenant = User.objects.create_user(
            email="t@example.com",
            password="StrongPass123!",
            full_name="T",
            role=User.Role.TENANT,
        )
        landlord = User.objects.create_user(
            email="l@example.com",
            password="StrongPass123!",
            full_name="L",
            role=User.Role.LANDLORD,
        )
        admin = User.objects.create_user(
            email="a@example.com",
            password="StrongPass123!",
            full_name="A",
            role=User.Role.ADMIN,
        )
        self.assertTrue(tenant.is_tenant)
        self.assertFalse(tenant.is_landlord)
        self.assertFalse(tenant.is_admin)
        self.assertTrue(landlord.is_landlord)
        self.assertFalse(landlord.is_tenant)
        self.assertTrue(admin.is_admin)
        self.assertFalse(admin.is_tenant)
        self.assertFalse(admin.is_landlord)


class UserModelConfigTests(django_tests.TestCase):
    def test_configured_auth_user_model(self):
        self.assertEqual(settings.AUTH_USER_MODEL, "accounts.User")

    def test_user_uses_email_as_username_field(self):
        self.assertEqual(User.USERNAME_FIELD, "email")

    def test_get_full_name_and_short_name(self):
        user = User.objects.create_user(
            email="name@example.com",
            password="StrongPass123!",
            full_name="Ada Lovelace",
        )
        self.assertEqual(user.get_full_name(), "Ada Lovelace")
        self.assertEqual(user.get_short_name(), "Ada Lovelace")

    def test_str_is_email(self):
        user = User.objects.create_user(
            email="str@example.com",
            password="StrongPass123!",
            full_name="String",
        )
        self.assertEqual(str(user), "str@example.com")
