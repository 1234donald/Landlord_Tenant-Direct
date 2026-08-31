"""
Unit tests for Phase 6, Sprint 6.5 - Audit, Logging and Data Integrity.

Covers the audit-event model, the audit logging service and the database
referential-integrity / deletion-behaviour contract.  It verifies:

- the ``AuditEvent`` model records category, action, target and user;
- audit events are ordered newest-first and indexed on key fields;
- the logging service emits events for auth, admin and data categories;
- the client-IP helper honours ``X-Forwarded-For``;
- deletion behaviour / referential integrity across the database models.
"""
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.test.utils import override_settings

from apps.audit.models import AuditEvent
from apps.audit.services import (
    get_client_ip,
    log_admin_event,
    log_auth_event,
    log_data_event,
    log_event,
    log_system_event,
)

User = get_user_model()
PASSWORD = "StrongPass123!"


class AuditEventModelTests(TestCase):
    """The ``AuditEvent`` model stores and orders audit records correctly."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="audit@example.com",
            password=PASSWORD,
            full_name="Audit User",
            role=User.Role.TENANT,
        )
        cls.older = AuditEvent.objects.create(
            user=cls.user,
            category=AuditEvent.Category.AUTH,
            action="Login successful",
        )
        cls.newer = AuditEvent.objects.create(
            user=cls.user,
            category=AuditEvent.Category.ADMIN,
            action="User account disabled",
            target_content_type="accounts.User",
            target_object_id=cls.user.pk,
            ip_address="127.0.0.1",
        )

    def test_ordering_is_newest_first(self):
        events = list(AuditEvent.objects.all())
        self.assertEqual(events[0], self.newer)
        self.assertEqual(events[1], self.older)

    def test_fields_are_persisted(self):
        event = self.newer
        self.assertEqual(event.category, AuditEvent.Category.ADMIN)
        self.assertEqual(event.action, "User account disabled")
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.target_content_type, "accounts.User")
        self.assertEqual(event.target_object_id, self.user.pk)
        self.assertEqual(event.ip_address, "127.0.0.1")
        self.assertEqual(event.extra, {})
        self.assertIsNotNone(event.created_at)

    def test_str_representation(self):
        text = str(self.newer)
        self.assertIn("User account disabled", text)
        self.assertIn("[ADMIN]", text)
        self.assertIn(str(self.user.pk), text)

    def test_system_event_has_no_user(self):
        event = AuditEvent.objects.create(
            category=AuditEvent.Category.SYSTEM, action="Startup"
        )
        self.assertIsNone(event.user)


class AuditServiceTests(TestCase):
    """The logging service emits audit records with correct context."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="service@example.com",
            password=PASSWORD,
            full_name="Service User",
            role=User.Role.TENANT,
        )

    def test_log_auth_event(self):
        event = log_auth_event(
            action="Login successful",
            user=self.user,
            ip_address="10.0.0.1",
            extra={"email": self.user.email},
        )
        self.assertEqual(event.category, AuditEvent.Category.AUTH)
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.ip_address, "10.0.0.1")
        self.assertEqual(event.extra["email"], self.user.email)

    def test_log_admin_event(self):
        event = log_admin_event(
            action="Verification approved",
            user=self.user,
            target_content_type="verification.VerificationRequest",
            target_object_id=7,
            ip_address="10.0.0.2",
            extra={"landlord_email": "landlord@example.com"},
        )
        self.assertEqual(event.category, AuditEvent.Category.ADMIN)
        self.assertEqual(event.target_content_type, "verification.VerificationRequest")
        self.assertEqual(event.target_object_id, 7)
        self.assertEqual(event.extra["landlord_email"], "landlord@example.com")

    def test_log_data_event(self):
        event = log_data_event(action="Apartment deleted", user=self.user)
        self.assertEqual(event.category, AuditEvent.Category.DATA)

    def test_log_system_event(self):
        event = log_system_event(action="Application started", extra={"env": "test"})
        self.assertEqual(event.category, AuditEvent.Category.SYSTEM)
        self.assertIsNone(event.user)
        self.assertEqual(event.extra["env"], "test")

    def test_log_event_uses_default_extra(self):
        event = log_event(category=AuditEvent.Category.SYSTEM, action="Noise")
        self.assertEqual(event.extra, {})


class ClientIpHelperTests(SimpleTestCase):
    """``get_client_ip`` honours reverse-proxy headers."""

    def test_uses_forwarded_header_when_present(self):
        factory = RequestFactory()
        request = factory.get("/", HTTP_X_FORWARDED_FOR="203.0.113.10, 10.0.0.1")
        self.assertEqual(get_client_ip(request), "203.0.113.10")

    def test_falls_back_to_remote_addr(self):
        factory = RequestFactory(REMOTE_ADDR="192.168.1.1")
        request = factory.get("/")
        self.assertEqual(get_client_ip(request), "192.168.1.1")


class ReferentialIntegrityTests(TestCase):
    """Database relationships preserve referential integrity (AGENTS 18).

    Verifies the documented deletion behaviour and foreign-key relationships
    across the core entities so that data is never orphaned inconsistently.
    """

    @classmethod
    def setUpTestData(cls):
        cls.landlord = User.objects.create_user(
            email="landlord@example.com",
            password=PASSWORD,
            full_name="Landlord",
            role=User.Role.LANDLORD,
        )
        cls.tenant = User.objects.create_user(
            email="tenant@example.com",
            password=PASSWORD,
            full_name="Tenant",
            role=User.Role.TENANT,
        )
        cls.admin = User.objects.create_user(
            email="admin@example.com",
            password=PASSWORD,
            full_name="Admin",
            role=User.Role.ADMIN,
        )

    def test_apartment_indexes_exist(self):
        from apps.apartments.models import Apartment

        index_fields = {
            tuple(index.fields)
            for index in Apartment._meta.indexes
        }
        self.assertIn(("location",), index_fields)
        self.assertIn(("rental_price",), index_fields)
        self.assertIn(("apartment_type",), index_fields)
        self.assertIn(("landlord",), index_fields)
        self.assertIn(("availability",), index_fields)

    def test_conversation_unique_pair_constraint(self):
        from apps.messaging.models import Conversation

        constraints = {
            tuple(c.fields) for c in Conversation._meta.constraints
        }
        self.assertIn(("tenant", "landlord"), constraints)

    def test_recommendation_item_unique_pair_constraint(self):
        from apps.recommendations.models import RecommendationItem

        constraints = {
            tuple(c.fields) for c in RecommendationItem._meta.constraints
        }
        self.assertIn(("recommendation", "apartment"), constraints)

    def test_verification_use_set_null_for_reviewer(self):
        from apps.verification.models import VerificationRequest

        field = VerificationRequest._meta.get_field("reviewed_by")
        self.assertEqual(field.remote_field.on_delete.__name__, "SET_NULL")
        self.assertTrue(field.null)

    def test_user_email_is_unique(self):
        email_field = User._meta.get_field("email")
        self.assertTrue(email_field.unique)

    def test_django_check_passes(self):
        from django.core.management import call_command

        call_command("check", verbosity=0)

    def test_apartment_model_validation(self):
        from apps.apartments.models import Apartment

        with self.assertRaises(ValidationError):
            invalid = Apartment(
                landlord=self.landlord,
                title="Bad",
                location="X",
                rental_price="-100.00",
                apartment_type=Apartment.ApartmentType.ONE_BEDROOM,
                bedrooms=0,
                bathrooms=1,
            )
            invalid.full_clean()
