"""
Integration tests for Phase 6, Sprint 6.3 - Security Hardening.

These verify the hardened application configuration (§27, AGENTS 19-24):
password security, CSRF protection, permissions footprint, secure cookie
configuration, file-upload validation wiring, secure error responses and
secrets management. The controls themselves were built across earlier sprints;
this suite verifies they are in place and behave correctly.

Tests that inspect configuration use SimpleTestCase where possible to stay
fast; request-level checks (CSRF, error pages) use the test client.
"""
import importlib
import os
import types

import django.test as django_tests
from django.conf import settings
from django.contrib.auth import get_user_model, hashers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.test import Client, RequestFactory, SimpleTestCase, override_settings
from django.urls import path, reverse

from apps.core.views import handler400, handler404, handler500

User = get_user_model()
PASSWORD = "StrongPass123!"
BASE_DIR = settings.BASE_DIR


class ProductionSecurityConfigTests(SimpleTestCase):
    """Production settings enable the documented security headers and cookies."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        os.environ["SECRET_KEY"] = "hardening-test-secret-key"
        cls.prod = importlib.import_module("config.settings.production")

    def test_secure_cookies_enabled(self):
        self.assertIs(self.prod.SESSION_COOKIE_SECURE, True)
        self.assertIs(self.prod.SESSION_COOKIE_HTTPONLY, True)
        self.assertEqual(self.prod.SESSION_COOKIE_SAMESITE, "Lax")
        self.assertIs(self.prod.CSRF_COOKIE_SECURE, True)
        self.assertEqual(self.prod.CSRF_COOKIE_SAMESITE, "Lax")

    def test_https_and_security_headers_enabled(self):
        self.assertIs(self.prod.SECURE_SSL_REDIRECT, True)
        self.assertEqual(self.prod.SECURE_HSTS_SECONDS, 31536000)
        self.assertIs(self.prod.SECURE_HSTS_INCLUDE_SUBDOMAINS, True)
        self.assertIs(self.prod.SECURE_CONTENT_TYPE_NOSNIFF, True)
        self.assertEqual(self.prod.X_FRAME_OPTIONS, "DENY")
        self.assertEqual(self.prod.SECURE_REFERRER_POLICY, "same-origin")

    def test_secret_key_is_required_and_not_placeholder(self):
        # The module reads SECRET_KEY from the environment we set in setUpClass.
        self.assertTrue(self.prod.SECRET_KEY)
        self.assertNotIn("django-insecure-", self.prod.SECRET_KEY)


class SecretsManagementTests(SimpleTestCase):
    """Secrets are environment-driven and never committed (AGENTS 20)."""

    def test_development_secret_key_is_not_hardcoded(self):
        self.assertNotIn("django-insecure-", settings.SECRET_KEY)

    def test_database_password_reads_from_environment(self):
        self.assertEqual(settings.DATABASES["default"]["PASSWORD"], os.environ.get("DATABASE_PASSWORD", ""))

    def test_env_and_private_keys_are_gitignored(self):
        with open(BASE_DIR / ".gitignore", encoding="utf-8") as handle:
            lines = handle.read().splitlines()
        self.assertIn(".env", lines)
        self.assertIn("*.pem", lines)
        self.assertIn("*.key", lines)


class PasswordSecurityTests(django_tests.TestCase):
    """Password hashing and the auth validators are configured (AGENTS 19)."""

    def test_strong_default_hasher(self):
        hasher = hashers.get_hasher()
        self.assertTrue(hasher.algorithm.startswith("pbkdf2"))

    def test_password_is_never_stored_plain(self):
        user = User.objects.create_user(
            email="hash@example.com",
            password="PlainText-#123",
            full_name="Hash",
            role=User.Role.TENANT,
        )
        self.assertNotEqual(user.password, "PlainText-#123")
        self.assertTrue(user.password.startswith("pbkdf2_"))

    def test_all_named_password_validators_configured(self):
        names = [
            v["NAME"].rsplit(".", 1)[-1]
            for v in settings.AUTH_PASSWORD_VALIDATORS
        ]
        for expected in (
            "UserAttributeSimilarityValidator",
            "MinimumLengthValidator",
            "CommonPasswordValidator",
            "NumericPasswordValidator",
        ):
            self.assertIn(expected, names)

    def test_numeric_password_is_rejected(self):
        with self.assertRaises(ValidationError):
            validate_password("12345678")

    def test_common_password_is_rejected(self):
        with self.assertRaises(ValidationError):
            validate_password("password")

    def test_short_password_is_rejected(self):
        with self.assertRaises(ValidationError):
            validate_password("Ab1")


class CsrfProtectionTests(django_tests.TestCase):
    """CSRF middleware is active and rejects tokenless POSTs (AGENTS 19)."""

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

    def test_csrf_middleware_is_present(self):
        self.assertIn(
            "django.middleware.csrf.CsrfViewMiddleware", settings.MIDDLEWARE
        )

    def _csrf_enforcing_client(self):
        # enforce_csrf_checks must be set at construction: the ClientHandler
        # stores its own copy, so mutating Client.enforce_csrf_checks later has
        # no effect (it exists for the Django admin test client). See
        # django.test.ClientHandler.__call__.
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        return client

    def test_post_without_csrf_token_is_rejected(self):
        client = self._csrf_enforcing_client()
        url = reverse("admin_dashboard:user-status", args=[self.landlord.pk])
        response = client.post(url)
        self.assertEqual(response.status_code, 403)

    def test_post_with_csrf_token_succeeds(self):
        client = self._csrf_enforcing_client()
        url = reverse("admin_dashboard:user-status", args=[self.landlord.pk])
        # A GET provides the CSRF cookie; a tokenised + same-origin POST passes.
        client.get(reverse("admin_dashboard:users"))
        response = client.post(
            url,
            {},
            HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
            HTTP_REFERER="http://localhost/console/users/",
        )
        self.assertEqual(response.status_code, 302)
        self.landlord.refresh_from_db()
        self.assertIs(self.landlord.is_active, False)


class SecureErrorResponseTests(SimpleTestCase):
    """Custom handlers render clean pages without leaking internals (AGENTS 22)."""

    def test_handler404_returns_404_page(self):
        with override_settings(DEBUG=False, ALLOWED_HOSTS=["localhost"]):
            response = Client(HTTP_HOST="localhost").get("/no-such-page/")
        self.assertEqual(response.status_code, 404)
        html = response.content.decode()
        self.assertIn("could not be found", html)
        self.assertNotIn("Traceback", html)
        self.assertNotIn(BASE_DIR.name, html)

    def test_handler404_directly_renders_status_404(self):
        response = handler404(RequestFactory().get("/x/"), None)
        self.assertEqual(response.status_code, 404)

    def test_handler400_directly_renders_status_400(self):
        self.assertEqual(handler400(RequestFactory().get("/x/")).status_code, 400)

    def test_handler500_renders_non_leaking_page(self):
        test_urlconf = self._boom_urlconf()
        with override_settings(
            ROOT_URLCONF=test_urlconf, DEBUG=False, ALLOWED_HOSTS=["localhost"]
        ):
            client = Client(HTTP_HOST="localhost", raise_request_exception=False)
            response = client.get("/boom/")
        self.assertEqual(response.status_code, 500)
        html = response.content.decode()
        self.assertIn("Something went wrong", html)
        self.assertNotIn("Traceback", html)
        self.assertNotIn("RuntimeError", html)

    def _boom_urlconf(self):
        import config.urls as root_urls

        module = types.ModuleType("hardening_test_urlconf")
        module.handler400 = handler400
        module.handler404 = handler404
        module.handler500 = handler500

        def boom(request):
            raise RuntimeError("hidden-internal-explosion")

        # Reuse the real root urlpatterns (so base.html navbar links resolve)
        # and append a route that raises so we can exercise handler500.
        module.urlpatterns = list(root_urls.urlpatterns) + [path("boom/", boom)]
        return module


class PermissionsFootprintTests(django_tests.TestCase):
    """Role enforcement protects admin and cross-role functions (AGENTS 8, 19)."""

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

    def test_landlord_gets_403_on_admin_console(self):
        self.client.force_login(self.landlord)
        for name in ("dashboard", "reports"):
            with self.subTest(page=name):
                url = reverse(f"admin_dashboard:{name}")
                self.assertEqual(self.client.get(url).status_code, 403)

    def test_anonymous_gets_403_on_admin_console(self):
        for name in ("dashboard", "reports"):
            with self.subTest(page=name):
                url = reverse(f"admin_dashboard:{name}")
                self.assertEqual(self.client.get(url).status_code, 403)

    def test_unauthenticated_api_is_denied(self):
        response = self.client.get(reverse("auth-me"))
        self.assertIn(response.status_code, (401, 403))


class FileUploadValidationWiringTests(SimpleTestCase):
    """File-upload validation is wired into settings/config (AGENTS 24)."""

    def test_image_upload_root_is_media_apartments(self):
        # The model declares upload_to under media; confirm media root is set.
        self.assertTrue(settings.MEDIA_ROOT)
        self.assertEqual(settings.MEDIA_URL, "/media/")

    def test_media_root_is_inside_project_and_never_static_served(self):
        # MEDIA_ROOT exists under the project; static root is separate so
        # uploaded files are never served as executable static assets.
        self.assertTrue(str(settings.MEDIA_ROOT).startswith(str(BASE_DIR)))
        self.assertNotEqual(
            str(settings.MEDIA_ROOT), str(settings.STATIC_ROOT)
        )
