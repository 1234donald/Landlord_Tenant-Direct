"""
Unit tests for Phase 7, Sprint 7.1 - Accounts serializers.

These construct the DRF serializers directly (the project's form/validation
layer, since no Django ``Form`` classes exist) and assert validation and
representation behaviour without needing the HTTP layer: email uniqueness,
ADMIN-role rejection, password validation for ``RegisterSerializer``; read-only
identity fields for ``ProfileSerializer``; and credential/inactive/JWT handling
for ``LoginSerializer`` (SYSTEM_REQUIREMENTS 41, AGENTS 23).
"""
import django.test as django_tests
from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.accounts.serializers import (
    LoginSerializer,
    ProfileSerializer,
    RegisterSerializer,
)

User = get_user_model()
PASSWORD = "StrongPass123!"


def make_user(email="existing@example.com", role=User.Role.TENANT):
    return User.objects.create_user(
        email=email,
        password=PASSWORD,
        full_name="Existing User",
        role=role,
    )


class RegisterSerializerTests(django_tests.TestCase):
    def _context(self, **request_data):
        # RegisterSerializer.create uses create_user and does not require a
        # request context; validation is independent of context.
        return {}

    def valid_payload(self, **overrides):
        payload = {
            "email": "new@example.com",
            "full_name": "New User",
            "phone": "08012345678",
            "password": PASSWORD,
            "role": User.Role.TENANT,
        }
        payload.update(overrides)
        return payload

    def test_valid_registration_data_is_accepted(self):
        serializer = RegisterSerializer(data=self.valid_payload())
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_email_is_normalised_to_lowercase(self):
        serializer = RegisterSerializer(
            data=self.valid_payload(email="New@Example.COM")
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["email"], "new@example.com")

    def test_duplicate_email_is_rejected(self):
        make_user(email="new@example.com")
        serializer = RegisterSerializer(data=self.valid_payload())
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_admin_role_is_rejected(self):
        serializer = RegisterSerializer(
            data=self.valid_payload(role=User.Role.ADMIN)
        )
        # ADMIN is not a valid choice at all for this field.
        self.assertFalse(serializer.is_valid())

    def test_weak_password_is_rejected(self):
        serializer = RegisterSerializer(
            data=self.valid_payload(password="short")
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

    def test_missing_required_fields_are_rejected(self):
        serializer = RegisterSerializer(data={})
        self.assertFalse(serializer.is_valid())
        for field in ("email", "full_name", "password"):
            self.assertIn(field, serializer.errors)

    def test_create_makes_user_with_provided_role(self):
        serializer = RegisterSerializer(data=self.valid_payload())
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.email, "new@example.com")
        self.assertEqual(user.role, User.Role.TENANT)
        self.assertTrue(user.check_password(PASSWORD))

    def test_to_representation_shape(self):
        user = make_user()
        representation = RegisterSerializer().to_representation(user)
        self.assertEqual(representation["id"], user.pk)
        self.assertEqual(representation["email"], user.email)
        self.assertEqual(representation["full_name"], user.full_name)
        self.assertIn("role", representation)


class ProfileSerializerTests(django_tests.TestCase):
    def test_identity_fields_are_read_only(self):
        user = make_user()
        serializer = ProfileSerializer(user)
        self.assertTrue(serializer.fields["email"].read_only)
        self.assertTrue(serializer.fields["role"].read_only)
        self.assertTrue(serializer.fields["is_active"].read_only)
        self.assertTrue(serializer.fields["id"].read_only)

    def test_read_representation_includes_identity(self):
        user = make_user()
        data = ProfileSerializer(user).data
        self.assertEqual(data["email"], user.email)
        self.assertEqual(data["role"], user.role)
        self.assertTrue(data["is_active"])


class LoginSerializerTests(django_tests.TestCase):
    def test_invalid_credentials_are_rejected(self):
        make_user()
        serializer = LoginSerializer(
            data={"email": "existing@example.com", "password": "WrongPass123!"}
        )
        self.assertFalse(serializer.is_valid())

    def test_valid_credentials_issue_jwt_tokens(self):
        make_user()
        serializer = LoginSerializer(
            data={"email": "existing@example.com", "password": PASSWORD}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertIn("access", serializer.validated_data)
        self.assertIn("refresh", serializer.validated_data)
        self.assertEqual(
            serializer.validated_data["user"].email, "existing@example.com"
        )

    def test_inactive_account_is_rejected(self):
        user = make_user()
        user.is_active = False
        user.save(update_fields=["is_active"])
        serializer = LoginSerializer(
            data={"email": "existing@example.com", "password": PASSWORD}
        )
        self.assertFalse(serializer.is_valid())

    def test_email_lookup_is_case_insensitive(self):
        make_user()
        serializer = LoginSerializer(
            data={"email": "EXISTING@example.com", "password": PASSWORD}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
