"""Shared pytest fixtures (Sprint 7.2).

Provides reusable user factories so test modules (API, integration, ML) do not
each re-implement account creation. Tests that need a fresh database must
still be decorated with ``pytest.mark.django_db`` (or subclass a Django
``TestCase``/``APITestCase``, which already wraps each test in a transaction).
"""
import pytest

from django.contrib.auth import get_user_model

User = get_user_model()

PASSWORD = "StrongPass123!"


@pytest.fixture
def password():
    return PASSWORD


@pytest.fixture
def make_user(db):
    def _make(role, **overrides):
        defaults = {
            "email": f"{role.lower()}@example.com",
            "password": PASSWORD,
            "full_name": f"{role.title()} User",
            "role": role,
        }
        defaults.update(overrides)
        return User.objects.create_user(**defaults)

    return _make


@pytest.fixture
def make_tenant(make_user):
    return lambda **kw: make_user(User.Role.TENANT, **kw)


@pytest.fixture
def make_landlord(make_user):
    return lambda **kw: make_user(User.Role.LANDLORD, **kw)


@pytest.fixture
def make_admin(make_user):
    return lambda **kw: make_user(User.Role.ADMIN, **kw)
