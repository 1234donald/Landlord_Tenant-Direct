"""
Integration tests for Phase 6, Sprint 6.5 - Audit logging in real flows.

Verifies that the REST API and the administrator console emit audit events
for the key security and administrative actions:

- successful registration;
- successful login;
- failed login;
- logout;
- user status toggle (admin);
- apartment moderation (admin);
- verification approve/reject (admin);

Each test drives the real endpoint/view and then asserts an ``AuditEvent``
record with the expected category, action and target was persisted.
"""
import django.test as django_tests
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.apartments.models import Apartment
from apps.audit.models import AuditEvent
from apps.verification.models import VerificationRequest

User = get_user_model()
PASSWORD = "StrongPass123!"

LOGIN_URL = "/api/v1/auth/login/"
LOGOUT_URL = "/api/v1/auth/logout/"
REGISTER_URL = "/api/v1/auth/register/"


class AuthAuditFlowTests(django_tests.TestCase):
    """Registration, login and logout emit authentication audit events."""

    def test_successful_registration_emits_auth_event(self):
        client = APIClient()
        response = client.post(
            REGISTER_URL,
            {
                "email": "newtenant@example.com",
                "full_name": "New Tenant",
                "password": PASSWORD,
                "role": User.Role.TENANT,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        events = AuditEvent.objects.filter(category=AuditEvent.Category.AUTH)
        self.assertTrue(events.exists())
        self.assertTrue(
            events.filter(action__contains="Account registered").exists()
        )

    def test_successful_login_emits_auth_event(self):
        tenant = User.objects.create_user(
            email="login-tenant@example.com",
            password=PASSWORD,
            full_name="Login Tenant",
            role=User.Role.TENANT,
        )
        client = APIClient()
        response = client.post(
            LOGIN_URL,
            {"email": tenant.email, "password": PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        event = AuditEvent.objects.filter(action="Login successful").latest("created_at")
        self.assertEqual(event.category, AuditEvent.Category.AUTH)
        self.assertEqual(event.user, tenant)

    def test_failed_login_emits_auth_event(self):
        User.objects.create_user(
            email="fail@example.com",
            password=PASSWORD,
            full_name="Fail",
            role=User.Role.TENANT,
        )
        client = APIClient()
        response = client.post(
            LOGIN_URL,
            {"email": "fail@example.com", "password": "WrongPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertTrue(
            AuditEvent.objects.filter(action="Login failed").exists()
        )

    def test_logout_emits_auth_event(self):
        tenant = User.objects.create_user(
            email="logout@example.com",
            password=PASSWORD,
            full_name="Logout",
            role=User.Role.TENANT,
        )
        client = APIClient()
        login = client.post(
            LOGIN_URL,
            {"email": tenant.email, "password": PASSWORD},
            format="json",
        )
        refresh = login.data["data"]["refresh"]
        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login.data['data']['access']}"
        )
        response = client.post(LOGOUT_URL, {"refresh": refresh}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            AuditEvent.objects.filter(action="Logout successful").exists()
        )


class AdminAuditFlowTests(django_tests.TestCase):
    """The administrative actions emit audit events for accountability."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            email="admin@example.com",
            password=PASSWORD,
            full_name="Admin",
            role=User.Role.ADMIN,
        )
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
        cls.apartment = Apartment.objects.create(
            landlord=cls.landlord,
            title="Flat",
            location="Calabar",
            rental_price="250000.00",
            apartment_type=Apartment.ApartmentType.TWO_BEDROOM,
            bedrooms=2,
            bathrooms=2,
            availability=True,
        )

    def setUp(self):
        self.client.force_login(self.admin)

    def _latest_admin_event(self):
        return AuditEvent.objects.filter(
            category=AuditEvent.Category.ADMIN
        ).latest("created_at")

    def test_user_status_toggle_emits_admin_event(self):
        url = reverse("admin_dashboard:user-status", args=[self.tenant.pk])
        self.client.post(url)
        event = self._latest_admin_event()
        self.assertEqual(event.target_content_type, "accounts.User")
        self.assertEqual(event.target_object_id, self.tenant.pk)
        self.assertIn("disabled", event.action)
        self.assertEqual(event.user, self.admin)

    def test_apartment_moderation_emits_admin_event(self):
        url = reverse("admin_dashboard:apartment-moderate", args=[self.apartment.pk])
        self.client.post(url)
        event = self._latest_admin_event()
        self.assertEqual(event.target_content_type, "apartments.Apartment")
        self.assertEqual(event.target_object_id, self.apartment.pk)
        self.assertIn("hidden", event.action)

    def test_verification_approve_emits_admin_event(self):
        verification = VerificationRequest.objects.create(landlord=self.landlord)
        url = reverse("admin_dashboard:verification-review", args=[verification.pk])
        self.client.post(url, {"action": "approve"})
        event = self._latest_admin_event()
        self.assertEqual(event.target_content_type, "verification.VerificationRequest")
        self.assertEqual(event.target_object_id, verification.pk)
        self.assertIn("approved", event.action)

    def test_verification_reject_emits_admin_event(self):
        verification = VerificationRequest.objects.create(landlord=self.landlord)
        url = reverse("admin_dashboard:verification-review", args=[verification.pk])
        self.client.post(url, {"action": "reject", "remarks": "Missing docs"})
        event = self._latest_admin_event()
        self.assertIn("rejected", event.action)
        self.assertEqual(event.extra.get("remarks"), "Missing docs")

    def test_non_admin_actions_do_not_emit_admin_events(self):
        # A landlord cannot reach the admin console (403) and no audit event
        # should be created for a forbidden attempt.
        self.client.logout()
        self.client.force_login(self.landlord)
        url = reverse("admin_dashboard:user-status", args=[self.tenant.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            AuditEvent.objects.filter(
                category=AuditEvent.Category.ADMIN
            ).exists()
        )
