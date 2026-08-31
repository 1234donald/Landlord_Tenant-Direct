"""
Unit tests for Phase 7, Sprint 7.1 - Verification serializers.

These construct the DRF serializers directly and verify the verification
submission (information validation, pending-duplicate rejection, ``create``),
the review remarks field, and the read representation (landlord/reviewer email
sources) without the HTTP layer (SYSTEM_REQUIREMENTS 41, AGENTS 23).
"""
import django.test as django_tests
from django.contrib.auth import get_user_model

from apps.verification.models import VerificationRequest
from apps.verification.serializers import (
    VerificationRequestSerializer,
    VerificationReviewSerializer,
    VerificationSubmitSerializer,
)

User = get_user_model()
PASSWORD = "StrongPass123!"


def make_user(email, role):
    return User.objects.create_user(
        email=email, password=PASSWORD, full_name=email, role=role
    )


class _FakeRequest:
    def __init__(self, user):
        self.user = user


class VerificationSubmitSerializerTests(django_tests.TestCase):
    def setUp(self):
        self.landlord = make_user("landlord@example.com", User.Role.LANDLORD)
        self.context = {"request": _FakeRequest(self.landlord)}

    def test_valid_submission_is_accepted_and_creates(self):
        serializer = VerificationSubmitSerializer(
            data={"information": "Property owner with identification docs."},
            context=self.context,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        verification = serializer.save()
        self.assertEqual(verification.landlord, self.landlord)
        self.assertEqual(
            verification.information, "Property owner with identification docs."
        )
        self.assertEqual(verification.status, VerificationRequest.Status.PENDING)

    def test_blank_information_is_rejected(self):
        serializer = VerificationSubmitSerializer(
            data={"information": "   "}, context=self.context
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("information", serializer.errors)

    def test_missing_information_is_rejected(self):
        serializer = VerificationSubmitSerializer(
            data={}, context=self.context
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("information", serializer.errors)

    def test_duplicate_pending_submission_is_rejected(self):
        VerificationRequest.objects.create(landlord=self.landlord)
        serializer = VerificationSubmitSerializer(
            data={"information": "Second submission"},
            context=self.context,
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_new_submission_allowed_after_approval(self):
        previous = VerificationRequest.objects.create(landlord=self.landlord)
        previous.approve(admin=make_user("admin@example.com", User.Role.ADMIN))
        serializer = VerificationSubmitSerializer(
            data={"information": "Re-open for review"},
            context=self.context,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)


class VerificationReviewSerializerTests(django_tests.TestCase):
    def test_remarks_are_optional_and_blankable(self):
        self.assertTrue(
            VerificationReviewSerializer(data={}).is_valid()
        )
        self.assertTrue(
            VerificationReviewSerializer(data={"remarks": ""}).is_valid()
        )
        self.assertTrue(
            VerificationReviewSerializer(
                data={"remarks": "Missing documents"}
            ).is_valid()
        )


class VerificationRequestReadSerializerTests(django_tests.TestCase):
    def setUp(self):
        self.landlord = make_user("landlord@example.com", User.Role.LANDLORD)
        self.admin = make_user("admin@example.com", User.Role.ADMIN)
        self.request = VerificationRequest.objects.create(
            landlord=self.landlord, information="docs"
        )

    def test_read_serializer_is_read_only(self):
        serializer = VerificationRequestSerializer(self.request)
        for field in serializer.fields.values():
            self.assertTrue(field.read_only)

    def test_read_exposes_landlord_and_reviewer_emails(self):
        data = VerificationRequestSerializer(self.request).data
        self.assertEqual(data["landlord_email"], self.landlord.email)
        self.assertIsNone(data["reviewed_by_email"])

        self.request.approve(admin=self.admin)
        data = VerificationRequestSerializer(self.request).data
        self.assertEqual(data["reviewed_by_email"], self.admin.email)
        self.assertEqual(data["status"], VerificationRequest.Status.APPROVED)
