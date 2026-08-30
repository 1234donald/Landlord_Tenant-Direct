"""
Integration tests for Phase 6, Sprint 6.2 - Administrative Workflows.

These verify the admin action views behind the Sprint 6.1 console: user status
management, apartment moderation, verification administration and the
administrative reports page (SYSTEM_REQUIREMENTS §40; FR-005; AGENTS 6, 8, 19,
39). State changes delegate to model logic (``User.is_active``,
``Apartment.availability``, ``VerificationRequest.approve/reject``) and report
figures are computed from the real database - nothing is fabricated.
"""
import django.test as django_tests
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.messages import get_messages

from apps.apartments.models import Apartment
from apps.messaging.models import Conversation, Message
from apps.verification.models import VerificationRequest

User = get_user_model()
PASSWORD = "StrongPass123!"


class AdminWorkflowAccessTests(django_tests.TestCase):
    """Action and report routes are ADMIN-only (AGENTS 8, 19)."""

    def _make(self, email, role):
        return User.objects.create_user(
            email=email, password=PASSWORD, full_name=email, role=role
        )

    def setUp(self):
        self.admin = self._make("admin@example.com", User.Role.ADMIN)
        self.landlord = self._make("landlord@example.com", User.Role.LANDLORD)
        self.tenant = self._make("tenant@example.com", User.Role.TENANT)
        self.apartment = Apartment.objects.create(
            landlord=self.landlord,
            title="Flat",
            location="Calabar",
            rental_price="250000.00",
            apartment_type=Apartment.ApartmentType.TWO_BEDROOM,
            bedrooms=2,
            bathrooms=2,
            availability=True,
        )
        self.verification = VerificationRequest.objects.create(landlord=self.landlord)

    def _action_urls(self):
        return [
            reverse("admin_dashboard:user-status", args=[self.tenant.pk]),
            reverse("admin_dashboard:apartment-moderate", args=[self.apartment.pk]),
            reverse(
                "admin_dashboard:verification-review", args=[self.verification.pk]
            ),
        ]

    def test_POST_actions_require_admin(self):
        for url in self._action_urls():
            for user in (self.landlord, self.tenant):
                with self.subTest(url=url, role=user.role):
                    self.client.force_login(user)
                    self.assertEqual(self.client.post(url).status_code, 403)

    def test_POST_actions_block_anonymous(self):
        for url in self._action_urls():
            with self.subTest(url=url):
                self.assertEqual(self.client.post(url).status_code, 403)

    def test_actions_reject_GET_requests(self):
        self.client.force_login(self.admin)
        for url in self._action_urls():
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 405)

    def test_reports_require_admin(self):
        url = reverse("admin_dashboard:reports")
        self.client.force_login(self.landlord)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 403)


class UserStatusWorkflowTests(django_tests.TestCase):
    """User status management (activate/deactivate)."""

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

    def _toggle(self, user, method="post"):
        self.client.force_login(self.admin)
        url = reverse("admin_dashboard:user-status", args=[user.pk])
        return getattr(self.client, method)(url)

    def test_disable_then_enable_user(self):
        self.assertEqual(self.landlord.is_active, True)
        self._toggle(self.landlord)
        self.landlord.refresh_from_db()
        self.assertEqual(self.landlord.is_active, False)
        self._toggle(self.landlord)
        self.landlord.refresh_from_db()
        self.assertEqual(self.landlord.is_active, True)

    def test_deactivated_user_cannot_authenticate(self):
        self._toggle(self.landlord)
        logged_in = self.client.login(
            email="landlord@example.com", password=PASSWORD
        )
        # A disabled account is not accepted (is_active=False blocks auth).
        self.assertFalse(logged_in)

    def test_redirects_to_user_management(self):
        response = self._toggle(self.landlord)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("admin_dashboard:users"))
        messages = list(get_messages(response.wsgi_request))
        self.assertIn("User landlord@example.com disabled.", [m.message for m in messages])

    def test_admin_account_is_not_toggled(self):
        url = reverse("admin_dashboard:user-status", args=[self.admin.pk])
        self.client.force_login(self.admin)
        self.client.post(url)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.is_active, True)


class ApartmentModerationWorkflowTests(django_tests.TestCase):
    """Apartment moderation (hide/unhide a listing)."""

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

    def _moderate(self):
        self.client.force_login(self.admin)
        return self.client.post(
            reverse("admin_dashboard:apartment-moderate", args=[self.apartment.pk])
        )

    def test_hide_then_unhide_listing(self):
        self.assertEqual(self.apartment.availability, True)
        self._moderate()
        self.apartment.refresh_from_db()
        self.assertEqual(self.apartment.availability, False)
        self._moderate()
        self.apartment.refresh_from_db()
        self.assertEqual(self.apartment.availability, True)

    def test_action_preserves_listing_record(self):
        self._moderate()
        self.apartment.refresh_from_db()
        self.assertIsNotNone(self.apartment.pk)
        self.assertEqual(self.apartment.title, "Flat")


class VerificationWorkflowTests(django_tests.TestCase):
    """Verification administration (approve/reject)."""

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

    def _review(self, verification, action, **extra):
        self.client.force_login(self.admin)
        return self.client.post(
            reverse("admin_dashboard:verification-review", args=[verification.pk]),
            {"action": action, **extra},
        )

    def test_approve_pending_request(self):
        verification = VerificationRequest.objects.create(landlord=self.landlord)
        response = self._review(verification, "approve")
        verification.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(verification.status, VerificationRequest.Status.APPROVED)
        self.assertEqual(verification.reviewed_by, self.admin)
        self.assertIsNotNone(verification.reviewed_at)

    def test_reject_pending_request_with_remarks(self):
        verification = VerificationRequest.objects.create(landlord=self.landlord)
        response = self._review(verification, "reject", remarks="Missing documents")
        verification.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(verification.status, VerificationRequest.Status.REJECTED)
        self.assertEqual(verification.remarks, "Missing documents")
        self.assertEqual(verification.reviewed_by, self.admin)

    def test_already_reviewed_request_is_not_reviewed_again(self):
        verification = VerificationRequest.objects.create(landlord=self.landlord)
        verification.approve(admin=self.admin)
        before = verification.status
        response = self._review(verification, "reject", remarks="late remarks")
        verification.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(verification.status, before)
        self.assertEqual(verification.remarks, "")

    def test_unknown_action_is_rejected(self):
        verification = VerificationRequest.objects.create(landlord=self.landlord)
        response = self._review(verification, "bogus")
        verification.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(verification.status, VerificationRequest.Status.PENDING)


class AdminReportsTests(django_tests.TestCase):
    """Reports page reflects the real database (AGENTS 39)."""

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
        cls.hidden = Apartment.objects.create(
            landlord=cls.landlord,
            title="Hidden",
            location="Calabar",
            rental_price="100000.00",
            apartment_type=Apartment.ApartmentType.ONE_BEDROOM,
            bedrooms=1,
            bathrooms=1,
            availability=False,
        )
        cls.pending = VerificationRequest.objects.create(landlord=cls.landlord)
        cls.approved = VerificationRequest.objects.create(landlord=cls.landlord)
        cls.approved.approve(admin=cls.admin)
        cls.rejected = VerificationRequest.objects.create(landlord=cls.landlord)
        cls.rejected.reject(admin=cls.admin, remarks="rejected")
        cls.conversation = Conversation.objects.create(
            tenant=cls.tenant, landlord=cls.landlord
        )
        Message.objects.create(
            conversation=cls.conversation,
            sender=cls.tenant,
            recipient=cls.landlord,
            body="Hello",
        )

    def _reports(self):
        self.client.force_login(self.admin)
        return self.client.get(reverse("admin_dashboard:reports"))

    def test_reports_reflect_real_counts(self):
        response = self._reports()
        self.assertEqual(response.status_code, 200)
        ctx = response.context
        self.assertEqual(ctx["role_counts"], {
            User.Role.TENANT: 1,
            User.Role.LANDLORD: 1,
            User.Role.ADMIN: 1,
        })
        self.assertEqual(ctx["active_users"], 3)
        self.assertEqual(ctx["inactive_users"], 0)
        self.assertEqual(ctx["apartments_total"], 2)
        self.assertEqual(ctx["apartments_available"], 1)
        self.assertEqual(ctx["apartments_hidden"], 1)
        self.assertEqual(ctx["verification_counts"], {
            VerificationRequest.Status.PENDING: 1,
            VerificationRequest.Status.APPROVED: 1,
            VerificationRequest.Status.REJECTED: 1,
        })
        self.assertEqual(ctx["conversation_count"], 1)
        self.assertEqual(ctx["message_count"], 1)

    def test_reports_page_renders_key_sections(self):
        html = self._reports().content.decode()
        self.assertIn("Administrative Reports", html)
        self.assertIn("Verification funnel", html)
        self.assertIn("Messaging", html)
