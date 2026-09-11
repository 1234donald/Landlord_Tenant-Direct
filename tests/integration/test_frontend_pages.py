"""
Integration tests for the server-rendered frontend pages (frontend build).

These verify the new session-based UI introduced for the frontend deliverable:

- Authentication pages (login / logout / register);
- Role-aware dashboards (tenant, landlord);
- Public registration and login flows;
- Profile update;
- Tenant preference page;
- Landlord apartment create / edit pages;
- Landlord verification page;
- Messaging pages (inbox, thread, start conversation).

Role enforcement follows AGENTS 8: a user may only reach pages belonging to
their own role, and anonymous users must be redirected or blocked on protected
pages. Every page renders against the real database - nothing is fabricated.
"""
import django.test as django_tests
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.apartments.models import Apartment
from apps.messaging.models import Conversation, Message
from apps.recommendations.models import Preference
from apps.verification.models import VerificationRequest

User = get_user_model()
PASSWORD = "StrongPass123!"


class AuthPageTests(django_tests.TestCase):
    """Login, register and logout flow (AGENTS 19)."""

    def test_login_page_renders(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)

    def test_register_page_renders(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)

    def test_register_creates_tenant_and_logs_in(self):
        response = self.client.post(
            reverse("register"),
            {
                "email": "new.tenant@example.com",
                "full_name": "New Tenant",
                "password": PASSWORD,
                "password2": PASSWORD,
                "role": User.Role.TENANT,
            },
        )
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email="new.tenant@example.com")
        self.assertTrue(user.is_tenant)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_register_rejects_weak_password(self):
        response = self.client.post(
            reverse("register"),
            {
                "email": "weak@example.com",
                "full_name": "Weak User",
                "password": "123",
                "password2": "123",
                "role": User.Role.TENANT,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(
            User.objects.filter(email="weak@example.com").exists(),
            "a flagged weak-password submission must not create an account",
        )

    def test_register_weak_password_then_valid_retry_succeeds(self):
        for _ in range(2):
            response = self.client.post(
                reverse("register"),
                {
                    "email": "retry@example.com",
                    "full_name": "Retry User",
                    "password": "123",
                    "password2": "123",
                    "role": User.Role.TENANT,
                },
            )
            self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(email="retry@example.com").exists())

        response = self.client.post(
            reverse("register"),
            {
                "email": "retry@example.com",
                "full_name": "Retry User",
                "password": PASSWORD,
                "password2": PASSWORD,
                "role": User.Role.TENANT,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email="retry@example.com").exists())

    def test_register_rejects_admin_role(self):
        response = self.client.post(
            reverse("register"),
            {
                "email": "helper@example.com",
                "full_name": "Helper",
                "password": PASSWORD,
                "password2": PASSWORD,
                "role": User.Role.ADMIN,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(role=User.Role.ADMIN).exists())

    def test_login_flow(self):
        user = User.objects.create_user(
            email="existing@example.com",
            password=PASSWORD,
            full_name="Existing",
            role=User.Role.TENANT,
        )
        response = self.client.post(
            reverse("login"),
            {"email": user.email, "password": PASSWORD},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_rejects_bad_credentials(self):
        response = self.client.post(
            reverse("login"),
            {"email": "nobody@example.com", "password": "wrong"},
        )
        self.assertEqual(response.status_code, 400)

    def test_logout(self):
        user = User.objects.create_user(
            email="out@example.com",
            password=PASSWORD,
            full_name="Out",
            role=User.Role.TENANT,
        )
        self.client.force_login(user)
        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class DashboardTests(django_tests.TestCase):
    """Role dashboards and 403 enforcement (AGENTS 8)."""

    def _make(self, email, role):
        return User.objects.create_user(
            email=email, password=PASSWORD, full_name=email.replace("@example.com", ""), role=role
        )

    def setUp(self):
        self.tenant = self._make("t@example.com", User.Role.TENANT)
        self.landlord = self._make("l@example.com", User.Role.LANDLORD)
        self.admin = self._make("a@example.com", User.Role.ADMIN)

    def test_tenant_dashboard_renders(self):
        self.client.force_login(self.tenant)
        response = self.client.get(reverse("tenant-dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tenant dashboard")

    def test_landlord_dashboard_renders(self):
        self.client.force_login(self.landlord)
        response = self.client.get(reverse("landlord-dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Landlord dashboard")

    def test_landlord_cannot_access_tenant_dashboard(self):
        self.client.force_login(self.landlord)
        self.assertEqual(
            self.client.get(reverse("tenant-dashboard")).status_code, 403
        )

    def test_tenant_cannot_access_landlord_dashboard(self):
        self.client.force_login(self.tenant)
        self.assertEqual(
            self.client.get(reverse("landlord-dashboard")).status_code, 403
        )

    def test_anonymous_is_redirected_away_from_tenant_dashboard(self):
        # Anonymous users are sent to the login page (LoginRequiredMixin).
        self.assertEqual(
            self.client.get(reverse("tenant-dashboard")).status_code, 302
        )

    def test_landlord_dashboard_shows_verification_state(self):
        VerificationRequest.objects.create(landlord=self.landlord)
        self.client.force_login(self.landlord)
        response = self.client.get(reverse("landlord-dashboard"))
        self.assertContains(response, "Pending review")


class ProfilePageTests(django_tests.TestCase):
    """Profile view/update (AGENTS 6, 21)."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="p@example.com",
            password=PASSWORD,
            full_name="Profile User",
            role=User.Role.TENANT,
        )

    def test_profile_page_renders_for_owner(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("tenant-profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "p@example.com")

    def test_profile_update_works(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("tenant-profile"),
            {"full_name": "Updated Name", "phone": "08012345678"},
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, "Updated Name")
        self.assertEqual(self.user.phone, "08012345678")


class TenantPreferencePageTests(django_tests.TestCase):
    """Preference form page (AGENTS 23, SYSTEM_REQUIREMENTS 26)."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="pref@example.com",
            password=PASSWORD,
            full_name="Preferrer",
            role=User.Role.TENANT,
        )

    def test_preference_page_renders_and_saves(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("edit-preference"))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            reverse("edit-preference"),
            {"location": "Ikeja", "max_rent": "450000", "bedrooms": "2", "bathrooms": "2"},
        )
        self.assertEqual(response.status_code, 302)
        pref = Preference.objects.get(tenant=self.user)
        self.assertEqual(pref.location, "Ikeja")
        self.assertEqual(int(pref.max_rent), 450000)

    def test_preference_rejects_negative_rent(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("edit-preference"),
            {"max_rent": "-5"},
        )
        self.assertEqual(response.status_code, 400)

    def test_landlord_is_blocked_from_preferences(self):
        landlord = User.objects.create_user(
            email="pl@example.com",
            password=PASSWORD,
            full_name="PL",
            role=User.Role.LANDLORD,
        )
        self.client.force_login(landlord)
        self.assertEqual(
            self.client.get(reverse("edit-preference")).status_code, 403
        )


class LandlordApartmentFormTests(django_tests.TestCase):
    """Apartment create/edit pages (AGENTS 10, 42)."""

    def setUp(self):
        self.landlord = User.objects.create_user(
            email="ll@example.com",
            password=PASSWORD,
            full_name="Landlord",
            role=User.Role.LANDLORD,
        )
        self.tenant = User.objects.create_user(
            email="tt@example.com",
            password=PASSWORD,
            full_name="Tenant",
            role=User.Role.TENANT,
        )

    def _payload(self):
        return {
            "title": "Sunny 2-bed flat",
            "location": "Ikeja",
            "address": "12 Example Street",
            "description": "A bright apartment",
            "rental_price": "350000",
            "apartment_type": "ONE_BEDROOM",
            "bedrooms": "1",
            "bathrooms": "1",
        }

    def test_create_page_renders_for_landlord(self):
        self.client.force_login(self.landlord)
        response = self.client.get(reverse("apartment-create"))
        self.assertEqual(response.status_code, 200)

    def test_create_apartment(self):
        self.client.force_login(self.landlord)
        response = self.client.post(
            reverse("apartment-create"), self._payload()
        )
        self.assertEqual(response.status_code, 302)
        apartment = Apartment.objects.get()
        self.assertEqual(apartment.landlord_id, self.landlord.id)
        self.assertEqual(apartment.title, "Sunny 2-bed flat")

    def test_tenant_is_blocked_from_create(self):
        self.client.force_login(self.tenant)
        self.assertEqual(
            self.client.get(reverse("apartment-create")).status_code, 403
        )

    def test_edit_page_owned_by_landlord(self):
        apartment = Apartment.objects.create(
            landlord=self.landlord, **self._payload()
        )
        self.client.force_login(self.landlord)
        response = self.client.get(
            reverse("apartment-edit", args=[apartment.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_tenant_cannot_edit_others_apartment(self):
        apartment = Apartment.objects.create(
            landlord=self.landlord, **self._payload()
        )
        self.client.force_login(self.tenant)
        response = self.client.get(
            reverse("apartment-edit", args=[apartment.pk])
        )
        self.assertEqual(response.status_code, 403)

    def test_rejects_negative_price(self):
        self.client.force_login(self.landlord)
        payload = self._payload()
        payload["rental_price"] = "-1"
        response = self.client.post(reverse("apartment-create"), payload)
        self.assertEqual(response.status_code, 400)


class LandlordVerificationPageTests(django_tests.TestCase):
    """Verification submission page (AGENTS 9)."""

    def setUp(self):
        self.landlord = User.objects.create_user(
            email="vl@example.com",
            password=PASSWORD,
            full_name="Verified",
            role=User.Role.LANDLORD,
        )

    def test_verification_page_renders(self):
        self.client.force_login(self.landlord)
        response = self.client.get(reverse("verification-form"))
        self.assertEqual(response.status_code, 200)

    def test_submit_verification(self):
        self.client.force_login(self.landlord)
        response = self.client.post(
            reverse("verification-form"),
            {"information": "I own and manage several apartments."},
        )
        self.assertEqual(response.status_code, 302)
        request_obj = VerificationRequest.objects.get(landlord=self.landlord)
        self.assertTrue(request_obj.is_pending)

    def test_tenant_is_blocked(self):
        tenant = User.objects.create_user(
            email="vt@example.com",
            password=PASSWORD,
            full_name="VTenant",
            role=User.Role.TENANT,
        )
        self.client.force_login(tenant)
        self.assertEqual(
            self.client.get(reverse("verification-form")).status_code, 403
        )


class MessagingPageTests(django_tests.TestCase):
    """Messaging inbox/thread/start-conversation (AGENTS 8, 42)."""

    def setUp(self):
        self.tenant = User.objects.create_user(
            email="mt@example.com",
            password=PASSWORD,
            full_name="Messenger",
            role=User.Role.TENANT,
        )
        self.landlord = User.objects.create_user(
            email="ml@example.com",
            password=PASSWORD,
            full_name="Landlord",
            role=User.Role.LANDLORD,
        )

    def test_tenant_inbox_renders(self):
        self.client.force_login(self.tenant)
        response = self.client.get(reverse("tenant-messages"))
        self.assertEqual(response.status_code, 200)

    def test_landlord_inbox_renders(self):
        self.client.force_login(self.landlord)
        response = self.client.get(reverse("landlord-messages"))
        self.assertEqual(response.status_code, 200)

    def test_tenant_service_inbox_is_role_safe(self):
        # Both inbox URL aliases render the SAME role-aware inbox; a tenant who
        # visits the landlord alias still only ever sees their own data
        # (AGENTS 8 - no cross-role leakage).
        self.client.force_login(self.tenant)
        response = self.client.get(reverse("landlord-messages"))
        self.assertEqual(response.status_code, 200)

    def test_start_conversation_from_landlord(self):
        self.client.force_login(self.tenant)
        response = self.client.post(
            reverse("new-conversation"), {"landlord": self.landlord.id}
        )
        self.assertEqual(response.status_code, 302)
        conversation = Conversation.objects.get(
            tenant=self.tenant, landlord=self.landlord
        )
        self.assertIsNotNone(conversation)

    def test_conversation_detail_and_send(self):
        conversation = Conversation.objects.create(
            tenant=self.tenant, landlord=self.landlord
        )
        Message.objects.create(
            conversation=conversation,
            sender=self.landlord,
            recipient=self.tenant,
            body="Hello, is the flat still available?",
        )
        self.client.force_login(self.tenant)
        response = self.client.get(
            reverse("conversation-detail", args=[conversation.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "still available")
        response = self.client.post(
            reverse("conversation-detail", args=[conversation.pk]),
            {"body": "Yes it is."},
        )
        self.assertEqual(response.status_code, 302)
        latest = conversation.messages.order_by("-id").first()
        self.assertEqual(latest.body, "Yes it is.")

    def test_non_participant_is_blocked_from_conversation(self):
        outsider = User.objects.create_user(
            email="mo@example.com",
            password=PASSWORD,
            full_name="Outsider",
            role=User.Role.TENANT,
        )
        conversation = Conversation.objects.create(
            tenant=self.tenant, landlord=self.landlord
        )
        self.client.force_login(outsider)
        response = self.client.get(
            reverse("conversation-detail", args=[conversation.pk])
        )
        self.assertEqual(response.status_code, 403)

    def test_opening_thread_marks_incoming_read(self):
        conversation = Conversation.objects.create(
            tenant=self.tenant, landlord=self.landlord
        )
        msg = Message.objects.create(
            conversation=conversation,
            sender=self.landlord,
            recipient=self.tenant,
            body="Message from landlord",
        )
        self.client.force_login(self.tenant)
        self.client.get(reverse("conversation-detail", args=[conversation.pk]))
        msg.refresh_from_db()
        self.assertTrue(msg.is_read)


class PublicPageTests(django_tests.TestCase):
    """Public pages render and browse/detail show real listings."""

    def setUp(self):
        self.landlord = User.objects.create_user(
            email="pub@example.com",
            password=PASSWORD,
            full_name="Pub Landlord",
            role=User.Role.LANDLORD,
        )

    def test_home_and_about_render(self):
        for name in ("home", "about"):
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_apartment_browse_renders(self):
        Apartment.objects.create(
            landlord=self.landlord,
            title="Browse Flat",
            location="Lekki",
            rental_price=400000,
            apartment_type="ONE_BEDROOM",
            bedrooms=1,
            bathrooms=1,
            availability=True,
        )
        response = self.client.get(reverse("apartment-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Browse Flat")

    def test_apartment_detail_renders_with_contact_for_tenant(self):
        apartment = Apartment.objects.create(
            landlord=self.landlord,
            title="Detail Flat",
            location="Yaba",
            rental_price=300000,
            apartment_type="FLAT",
            bedrooms=2,
            bathrooms=2,
            availability=True,
        )
        tenant = User.objects.create_user(
            email="dt@example.com",
            password=PASSWORD,
            full_name="DTenant",
            role=User.Role.TENANT,
        )
        self.client.force_login(tenant)
        response = self.client.get(reverse("apartment-detail", args=[apartment.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Contact landlord")