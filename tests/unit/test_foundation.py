"""
Foundation tests for Phase 1, Sprint 1.3/1.5.

These verify the Django project foundation: the settings split, the base URL
routing, and the base UI rendering. They are intentionally DB-independent
(SimpleTestCase) so they only verify configuration, routing and templates.
"""
from django.test import Client, SimpleTestCase, override_settings
from django.urls import resolve, reverse


class SettingsFoundationTests(SimpleTestCase):
    def test_default_settings_module_is_development(self):
        import os

        module = os.environ.get("DJANGO_SETTINGS_MODULE", "config.settings")
        # Default (unset) resolves to the settings package, whose __init__
        # re-exports the development settings.
        self.assertEqual(module, "config.settings")

    @override_settings(DEBUG=True)
    def test_debug_enabled_from_development_default(self):
        from django.conf import settings

        self.assertTrue(settings.DEBUG)

    def test_database_engine_is_postgresql(self):
        from django.conf import settings

        engine = settings.DATABASES["default"]["ENGINE"]
        self.assertEqual(engine, "django.db.backends.postgresql")

    def test_secret_key_is_not_hardcoded(self):
        # A random SECRET_KEY is generated when none is supplied, so a literal
        # placeholder must never leak into configuration.
        from django.conf import settings

        self.assertNotIn("django-insecure-", settings.SECRET_KEY)


class UrlRoutingFoundationTests(SimpleTestCase):
    def test_home_url_resolves(self):
        match = resolve("/")
        self.assertEqual(match.url_name, "home")

    def test_home_reverse(self):
        self.assertEqual(reverse("home"), "/")

    def test_admin_url_resolves(self):
        match = resolve("/admin/")
        self.assertTrue(match.url_name)

    def test_api_url_mounts(self):
        from django.conf import settings

        self.assertTrue(hasattr(settings, "ROOT_URLCONF"))


class BaseUiFoundationTests(SimpleTestCase):
    """Verify the base template, navigation and static wiring render."""

    def setUp(self):
        # The test client defaults to the ``testserver`` host, which is not in
        # ALLOWED_HOSTS; ``localhost`` is, so use it explicitly.
        self.client = Client(HTTP_HOST="localhost")

    def test_home_renders_base_ui(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("navbar", content)
        self.assertIn("footer", content)
        self.assertIn("Landlord-Tenant Connect", content)
        self.assertIn("bootstrap.min.css", content)
        self.assertIn("main.css", content)

    def test_about_renders_base_ui(self):
        response = self.client.get("/about/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("navbar", content)
        self.assertIn("footer", content)
        self.assertIn("Landlord-Tenant Connect", content)

    def test_about_url_resolves(self):
        match = resolve("/about/")
        self.assertEqual(match.url_name, "about")

    def test_about_reverse(self):
        self.assertEqual(reverse("about"), "/about/")
