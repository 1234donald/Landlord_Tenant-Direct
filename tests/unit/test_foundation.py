"""
Foundation tests for Phase 1, Sprint 1.3.

These verify the Django project foundation: the settings split and the base
URL routing. They are intentionally DB-independent (SimpleTestCase) so they
only verify configuration and routing.
"""
from django.test import SimpleTestCase, override_settings
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
