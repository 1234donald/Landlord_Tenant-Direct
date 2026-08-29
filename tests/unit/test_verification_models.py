"""
Unit tests for Phase 3, Sprint 3.1 - Landlord Verification Data Model.

These verify the ``VerificationRequest`` model used by the administrative
landlord-verification workflow: the landlord relationship, the verification
status lifecycle, remarks, submission timestamp and the administrator review
relationship. They require a test database.
"""
import django.test as django_tests
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from apps.verification.models import VerificationRequest

User = get_user_model()

PASSWORD = "StrongPass123!"


def make_landlord(email="landlord@example.com"):
    return User.objects.create_user(
        email=email,
        password=PASSWORD,
        full_name="Landlord User",
        role=User.Role.LANDLORD,
    )


def make_admin(email="admin@example.com"):
    return User.objects.create_user(
        email=email,
        password=PASSWORD,
        full_name="Admin User",
        role=User.Role.ADMIN,
    )


class VerificationRequestModelTests(django_tests.TestCase):
    def setUp(self):
        self.landlord = make_landlord()

    def test_default_status_is_pending(self):
        request = VerificationRequest.objects.create(landlord=self.landlord)
        self.assertEqual(request.status, VerificationRequest.Status.PENDING)
        self.assertTrue(request.is_pending)

    def test_status_choices(self):
        self.assertEqual(
            set(VerificationRequest.Status.values),
            {"PENDING", "APPROVED", "REJECTED"},
        )

    def test_status_helper_properties(self):
        pending = VerificationRequest.objects.create(landlord=self.landlord)
        self.assertTrue(pending.is_pending)
        self.assertFalse(pending.is_approved)
        self.assertFalse(pending.is_rejected)

        approved = VerificationRequest.objects.create(
            landlord=self.landlord,
            status=VerificationRequest.Status.APPROVED,
        )
        self.assertTrue(approved.is_approved)
        self.assertFalse(approved.is_pending)

        rejected = VerificationRequest.objects.create(
            landlord=self.landlord,
            status=VerificationRequest.Status.REJECTED,
        )
        self.assertTrue(rejected.is_rejected)
        self.assertFalse(rejected.is_pending)

    def test_rejected_status_is_valid_choice(self):
        request = VerificationRequest(
            landlord=self.landlord,
            status="REJECTED",
        )
        # A status outside the declared choices must be rejected at the DB layer.
        request.full_clean()
        allowed = {
            choice[0] for choice in VerificationRequest.Status.choices
        }
        self.assertIn("REJECTED", allowed)

    def test_landlord_relationship(self):
        request = VerificationRequest.objects.create(landlord=self.landlord)
        self.assertEqual(request.landlord, self.landlord)
        self.assertIn(
            request,
            self.landlord.verification_requests.all(),
        )

    def test_verification_requires_a_landlord(self):
        with self.assertRaises(IntegrityError):
            VerificationRequest.objects.create()

    def test_admin_review_relationship(self):
        admin = make_admin()
        request = VerificationRequest.objects.create(landlord=self.landlord)
        request.reviewed_by = admin
        request.reviewed_at = None
        request.save()
        self.assertEqual(request.reviewed_by, admin)
        self.assertIn(request, admin.verification_reviews.all())

    def test_reviewed_by_set_null_on_admin_deletion(self):
        admin = make_admin()
        request = VerificationRequest.objects.create(landlord=self.landlord)
        request.reviewed_by = admin
        request.save()
        admin.delete()
        request.refresh_from_db()
        self.assertIsNone(request.reviewed_by)

    def test_submitted_at_populated_automatically(self):
        request = VerificationRequest.objects.create(landlord=self.landlord)
        self.assertIsNotNone(request.submitted_at)

    def test_remarks_and_information_are_blank_by_default(self):
        request = VerificationRequest.objects.create(landlord=self.landlord)
        self.assertEqual(request.remarks, "")
        self.assertEqual(request.information, "")

    def test_reviewed_at_null_by_default(self):
        request = VerificationRequest.objects.create(landlord=self.landlord)
        self.assertIsNone(request.reviewed_at)

    def test_string_representation(self):
        request = VerificationRequest.objects.create(landlord=self.landlord)
        self.assertIn("Verification for", str(request))
        self.assertIn("PENDING", str(request))

    def test_default_ordering_newest_first(self):
        a = VerificationRequest.objects.create(landlord=self.landlord)
        b = VerificationRequest.objects.create(landlord=self.landlord)
        self.assertEqual(
            list(VerificationRequest.objects.all()),
            [b, a],
        )

    def test_list_returns_newest_first(self):
        a = VerificationRequest.objects.create(landlord=self.landlord)
        b = VerificationRequest.objects.create(landlord=self.landlord)
        self.assertGreaterEqual(b.submitted_at, a.submitted_at)

    def test_model_has_no_legal_ownership_claim_fields(self):
        # The verification model is an administrative platform control only;
        # it must not expose fields that claim legal property-ownership
        # verification (AGENTS 9, 17, 37).
        field_names = {
            field.name
            for field in VerificationRequest._meta.get_fields()
        }
        for disallowed in ("ownership_document", "title_deed",
                           "legal_verified", "ownership_verified"):
            self.assertNotIn(disallowed, field_names)
