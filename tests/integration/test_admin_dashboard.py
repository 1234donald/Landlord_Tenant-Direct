"""
Integration tests for Phase 6, Sprint 6.1 - Administrator Dashboard.

These verify the admin-only presentation module: the system-overview dashboard,
user management, landlord management, apartment management and verification
overview pages (FR-005, AGENTS 42). They confirm role enforcement (ADMIN only;
landlords/tenants/anonymous blocked) and that the rendered overviews reflect
the actual database without fabricated statistics (AGENTS 39).
"""
import django.test as django_tests
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.apartments.models import Apartment
from apps.messaging.models import Conversation, Message
from apps.verification.models import VerificationRequest

User = get_user_model()
PASSWORD = "StrongPass123!"


class AdminDashboardAccessTests(django_tests.TestCase):
    """Only ADMIN users can reach the dashboard pages (AGENTS 8, 19)."""

    def _make(self, email, role):
        return User.objects.create_user(
            email=email, password=PASSWORD, full_name=email, role=role
        )

    def setUp(self):
        self.admin = self._make("admin@example.com", User.Role.ADMIN)
        self.landlord = self._make("landlord@example.com", User.Role.LANDLORD)
        self.tenant = self._make("tenant@example.com", User.Role.TENANT)

    def _urls(self):
        return [
            reverse("admin_dashboard:dashboard"),
            reverse("admin_dashboard:users"),
            reverse("admin_dashboard:landlords"),
            reverse("admin_dashboard:apartments"),
            reverse("admin_dashboard:verifications"),
        ]

    def test_admin_can_access_all_dashboard_pages(self):
        self.client.force_login(self.admin)
        for url in self._urls():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_landlord_is_blocked(self):
        self.client.force_login(self.landlord)
        for url in self._urls():
            with self.subTest(url=url):
                self.assertEqual(
                    self.client.get(url).status_code, 403
                )

    def test_tenant_is_blocked(self):
        self.client.force_login(self.tenant)
        for url in self._urls():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403)

    def test_anonymous_is_blocked(self):
        for url in self._urls():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403)


class AdminDashboardContentTests(django_tests.TestCase):
    """Dashboard overview reflects the real database (no fabricated stats)."""

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
        # One pending verification request.
        cls.verification = VerificationRequest.objects.create(
            landlord=cls.landlord, information="documents"
        )
        # One conversation and its message.
        cls.conversation = Conversation.objects.create(
            tenant=cls.tenant, landlord=cls.landlord
        )
        Message.objects.create(
            conversation=cls.conversation,
            sender=cls.tenant,
            recipient=cls.landlord,
            body="Hello",
        )

    def _dashboard(self):
        self.client.force_login(self.admin)
        return self.client.get(reverse("admin_dashboard:dashboard"))

    def test_dashboard_shows_user_counts(self):
        html = self._dashboard().content.decode()
        self.assertIn("Total users", html)
        self.assertIn("Tenants", html)
        self.assertIn("Landlords", html)
        self.assertIn("Administrators", html)

    def test_dashboard_reflects_real_counts(self):
        response = self._dashboard()
        context = response.context
        # 1 admin + 1 landlord + 1 tenant = 3 users; all active.
        self.assertEqual(context["total_users"], 3)
        self.assertEqual(context["active_users"], 3)
        self.assertEqual(context["tenant_count"], 1)
        self.assertEqual(context["landlord_count"], 1)
        self.assertEqual(context["admin_count"], 1)
        self.assertEqual(context["total_apartments"], 1)
        self.assertEqual(context["available_apartments"], 1)
        self.assertEqual(context["verification_pending"], 1)
        self.assertEqual(context["verification_approved"], 0)
        self.assertEqual(context["verification_rejected"], 0)
        self.assertEqual(context["total_conversations"], 1)
        self.assertEqual(context["total_messages"], 1)

    def test_dashboard_links_to_management_pages(self):
        # Auto-discovery of a fake badge would fail the "no fabricated stats"
        # rule; the quick-action links must point at the real management pages.
        response = self._dashboard()
        self.assertContains(response, reverse("admin_dashboard:users"))
        self.assertContains(response, reverse("admin_dashboard:landlords"))
        self.assertContains(response, reverse("admin_dashboard:apartments"))
        self.assertContains(response, reverse("admin_dashboard:verifications"))


class AdminManagementListTests(django_tests.TestCase):
    """Management lists render the correct users/apartments/verifications."""

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
            full_name="Landlord One",
            role=User.Role.LANDLORD,
        )
        cls.landlord2 = User.objects.create_user(
            email="l2@example.com",
            password=PASSWORD,
            full_name="Landlord Two",
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
            title="L1 flat",
            location="Calabar",
            rental_price="200000.00",
            apartment_type=Apartment.ApartmentType.TWO_BEDROOM,
            bedrooms=2,
            bathrooms=2,
            availability=True,
        )
        cls.pending = VerificationRequest.objects.create(landlord=cls.landlord)
        cls.approved = VerificationRequest.objects.create(landlord=cls.landlord2)
        cls.approved.status = VerificationRequest.Status.APPROVED
        cls.approved.reviewed_by = cls.admin
        cls.approved.save()

    def _login(self):
        self.client.force_login(self.admin)

    def test_user_management_renders_all_users(self):
        self._login()
        response = self.client.get(reverse("admin_dashboard:users"))
        self.assertEqual(response.status_code, 200)
        users = response.context["users"]
        self.assertEqual(users.count(), 4)
        self.assertContains(response, "tenant@example.com")
        self.assertContains(response, "admin@example.com")

    def test_user_management_role_filter(self):
        self._login()
        response = self.client.get(
            reverse("admin_dashboard:users"), {"role": User.Role.LANDLORD}
        )
        role_emails = {
            u.email for u in response.context["users"]
        }
        self.assertEqual(role_emails, {"landlord@example.com", "l2@example.com"})

    def test_landlord_management_renders_landlords(self):
        self._login()
        response = self.client.get(reverse("admin_dashboard:landlords"))
        self.assertEqual(response.status_code, 200)
        landlords = list(response.context["landlords"])
        self.assertEqual(len(landlords), 2)
        self.assertContains(response, "Landlord One")

    def test_apartment_management_renders_all_listings(self):
        self._login()
        response = self.client.get(reverse("admin_dashboard:apartments"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["apartments"].count(), 1)
        self.assertContains(response, "L1 flat")

    def test_verification_overview_defaults_to_pending(self):
        self._login()
        response = self.client.get(reverse("admin_dashboard:verifications"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["status"], VerificationRequest.Status.PENDING)
        verifications = list(response.context["verifications"])
        self.assertEqual(len(verifications), 1)
        self.assertEqual(verifications[0].pk, self.pending.pk)

    def test_verification_overview_status_filter(self):
        self._login()
        response = self.client.get(
            reverse("admin_dashboard:verifications"),
            {"status": VerificationRequest.Status.APPROVED},
        )
        verifications = list(response.context["verifications"])
        self.assertEqual(len(verifications), 1)
        self.assertEqual(verifications[0].pk, self.approved.pk)
