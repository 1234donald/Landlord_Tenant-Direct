"""
Unit tests for Phase 7, Sprint 7.1 - Permission classes.

These instantiate every permission class directly and exercise
``has_permission`` and ``has_object_permission`` for all role combinations
using lightweight stub requests/users/objects (no database, no HTTP). They
verify the role-based access-control rules (AGENTS 8, 19) at the permission
level: only the correct role passes ``has_permission``, and object-level rules
(owner, participant, sender/recipient, admin bypass) are enforced
(SYSTEM_REQUIREMENTS 41).
"""
from types import SimpleNamespace

import django.test as django_tests

from apps.accounts.permissions import IsAdmin, IsLandlord, IsOwnerOrAdmin, IsTenant
from apps.apartments.permissions import IsApartmentOwnerOrAdmin
from apps.messaging.permissions import (
    IsConversationParticipantOrAdmin,
    IsParticipantForMessage,
)
from apps.recommendations.permissions import (
    IsPreferenceOwnerOrAdmin,
    IsRecommendationOwnerOrAdmin,
)


def anon_user():
    return SimpleNamespace(
        is_authenticated=False, is_tenant=False, is_landlord=False,
        is_admin=False, id=None, pk=None,
    )


def role_user(role, user_id=1):
    return SimpleNamespace(
        is_authenticated=True,
        is_tenant=(role == "TENANT"),
        is_landlord=(role == "LANDLORD"),
        is_admin=(role == "ADMIN"),
        id=user_id,
        pk=user_id,
    )


def request_for(user):
    return SimpleNamespace(user=user)


def make_obj(**kwargs):
    return SimpleNamespace(**kwargs)


class TestRolePermissionClasses(django_tests.TestCase):
    """has_permission for the role gatekeepers (IsTenant, IsLandlord, IsAdmin)."""

    def test_IsTenant_requires_authenticated_tenant(self):
        permission = IsTenant()
        self.assertTrue(
            permission.has_permission(request_for(role_user("TENANT")), None)
        )
        self.assertFalse(
            permission.has_permission(request_for(role_user("LANDLORD")), None)
        )
        self.assertFalse(
            permission.has_permission(request_for(role_user("ADMIN")), None)
        )
        self.assertFalse(
            permission.has_permission(request_for(anon_user()), None)
        )

    def test_IsLandlord_requires_authenticated_landlord(self):
        permission = IsLandlord()
        self.assertTrue(
            permission.has_permission(request_for(role_user("LANDLORD")), None)
        )
        self.assertFalse(
            permission.has_permission(request_for(role_user("TENANT")), None)
        )
        self.assertFalse(
            permission.has_permission(request_for(role_user("ADMIN")), None)
        )
        self.assertFalse(
            permission.has_permission(request_for(anon_user()), None)
        )

    def test_IsAdmin_requires_authenticated_admin(self):
        permission = IsAdmin()
        self.assertTrue(
            permission.has_permission(request_for(role_user("ADMIN")), None)
        )
        self.assertFalse(
            permission.has_permission(request_for(role_user("TENANT")), None)
        )
        self.assertFalse(
            permission.has_permission(request_for(role_user("LANDLORD")), None)
        )
        self.assertFalse(
            permission.has_permission(request_for(anon_user()), None)
        )


class TestIsOwnerOrAdmin(django_tests.TestCase):
    def setUp(self):
        self.permission = IsOwnerOrAdmin()

    def test_has_permission_requires_authentication(self):
        self.assertTrue(
            self.permission.has_permission(request_for(role_user("TENANT")), None)
        )
        self.assertFalse(self.permission.has_permission(request_for(anon_user()), None))

    def test_object_allows_owner(self):
        owner = role_user("TENANT", 5)
        obj = make_obj(pk=5)
        self.assertTrue(
            self.permission.has_object_permission(request_for(owner), None, obj)
        )

    def test_object_denies_non_owner(self):
        other = role_user("TENANT", 9)
        obj = make_obj(pk=5)
        self.assertFalse(
            self.permission.has_object_permission(request_for(other), None, obj)
        )

    def test_object_allows_admin(self):
        admin = role_user("ADMIN", 1)
        obj = make_obj(pk=5)
        self.assertTrue(
            self.permission.has_object_permission(request_for(admin), None, obj)
        )

    def test_object_denies_anonymous(self):
        obj = make_obj(pk=5)
        self.assertFalse(
            self.permission.has_object_permission(request_for(anon_user()), None, obj)
        )


class TestIsApartmentOwnerOrAdmin(django_tests.TestCase):
    def setUp(self):
        self.permission = IsApartmentOwnerOrAdmin()

    def test_has_permission_requires_authentication(self):
        self.assertTrue(
            self.permission.has_permission(request_for(role_user("LANDLORD")), None)
        )
        self.assertFalse(self.permission.has_permission(request_for(anon_user()), None))

    def test_object_allows_owning_landlord(self):
        owner = role_user("LANDLORD", 3)
        apartment = make_obj(landlord=owner, landlord_id=3)
        self.assertTrue(
            self.permission.has_object_permission(request_for(owner), None, apartment)
        )

    def test_object_denies_other_landlord(self):
        other = role_user("LANDLORD", 8)
        apartment = make_obj(landlord_id=3)
        self.assertFalse(
            self.permission.has_object_permission(request_for(other), None, apartment)
        )

    def test_object_denies_tenant(self):
        tenant = role_user("TENANT", 1)
        apartment = make_obj(landlord_id=3)
        self.assertFalse(
            self.permission.has_object_permission(request_for(tenant), None, apartment)
        )

    def test_object_allows_admin(self):
        admin = role_user("ADMIN", 1)
        apartment = make_obj(landlord_id=3)
        self.assertTrue(
            self.permission.has_object_permission(request_for(admin), None, apartment)
        )


class TestIsConversationParticipantOrAdmin(django_tests.TestCase):
    def setUp(self):
        self.permission = IsConversationParticipantOrAdmin()

    def test_object_allows_participant(self):
        tenant = role_user("TENANT", 1)
        conversation = make_obj(
            is_participant=lambda u: u.id == 1
        )
        self.assertTrue(
            self.permission.has_object_permission(request_for(tenant), None, conversation)
        )

    def test_object_denies_non_participant(self):
        outsider = role_user("LANDLORD", 9)
        conversation = make_obj(
            is_participant=lambda u: u.id == 1
        )
        self.assertFalse(
            self.permission.has_object_permission(request_for(outsider), None, conversation)
        )

    def test_object_allows_admin_even_if_not_participant(self):
        admin = role_user("ADMIN", 1)
        conversation = make_obj(
            is_participant=lambda u: u.id == 999
        )
        self.assertTrue(
            self.permission.has_object_permission(request_for(admin), None, conversation)
        )

    def test_has_permission_requires_authentication(self):
        self.assertTrue(
            self.permission.has_permission(request_for(role_user("TENANT")), None)
        )
        self.assertFalse(self.permission.has_permission(request_for(anon_user()), None))


class TestIsParticipantForMessage(django_tests.TestCase):
    def setUp(self):
        self.permission = IsParticipantForMessage()

    def test_object_allows_sender(self):
        sender = role_user("TENANT", 2)
        message = make_obj(sender=sender, recipient=None, sender_id=2, recipient_id=7)
        self.assertTrue(
            self.permission.has_object_permission(request_for(sender), None, message)
        )

    def test_object_allows_recipient(self):
        recipient = role_user("LANDLORD", 7)
        message = make_obj(sender=None, recipient=recipient, sender_id=2, recipient_id=7)
        self.assertTrue(
            self.permission.has_object_permission(request_for(recipient), None, message)
        )

    def test_object_denies_unrelated_user(self):
        other = role_user("TENANT", 9)
        message = make_obj(sender=None, recipient=None, sender_id=2, recipient_id=7)
        self.assertFalse(
            self.permission.has_object_permission(request_for(other), None, message)
        )

    def test_object_allows_admin(self):
        admin = role_user("ADMIN", 1)
        message = make_obj(sender=None, recipient=None, sender_id=2, recipient_id=7)
        self.assertTrue(
            self.permission.has_object_permission(request_for(admin), None, message)
        )


class TestPreferenceOwnerOrAdmin(django_tests.TestCase):
    def setUp(self):
        self.permission = IsPreferenceOwnerOrAdmin()

    def test_object_allows_owning_tenant(self):
        owner = role_user("TENANT", 4)
        preference = make_obj(tenant=owner, tenant_id=4)
        self.assertTrue(
            self.permission.has_object_permission(request_for(owner), None, preference)
        )

    def test_object_denies_other_tenant(self):
        other = role_user("TENANT", 9)
        preference = make_obj(tenant=None, tenant_id=4)
        self.assertFalse(
            self.permission.has_object_permission(request_for(other), None, preference)
        )

    def test_object_denies_landlord(self):
        landlord = role_user("LANDLORD", 2)
        preference = make_obj(tenant=None, tenant_id=4)
        self.assertFalse(
            self.permission.has_object_permission(request_for(landlord), None, preference)
        )

    def test_object_allows_admin(self):
        admin = role_user("ADMIN", 1)
        preference = make_obj(tenant=None, tenant_id=4)
        self.assertTrue(
            self.permission.has_object_permission(request_for(admin), None, preference)
        )


class TestRecommendationOwnerOrAdmin(django_tests.TestCase):
    def setUp(self):
        self.permission = IsRecommendationOwnerOrAdmin()

    def test_object_allows_owning_tenant(self):
        owner = role_user("TENANT", 4)
        recommendation = make_obj(tenant=owner, tenant_id=4)
        self.assertTrue(
            self.permission.has_object_permission(request_for(owner), None, recommendation)
        )

    def test_object_denies_other_tenant(self):
        other = role_user("TENANT", 6)
        recommendation = make_obj(tenant=None, tenant_id=4)
        self.assertFalse(
            self.permission.has_object_permission(
                request_for(other), None, recommendation
            )
        )

    def test_object_denies_landlord(self):
        landlord = role_user("LANDLORD", 2)
        recommendation = make_obj(tenant=None, tenant_id=4)
        self.assertFalse(
            self.permission.has_object_permission(
                request_for(landlord), None, recommendation
            )
        )

    def test_object_allows_admin(self):
        admin = role_user("ADMIN", 1)
        recommendation = make_obj(tenant=None, tenant_id=4)
        self.assertTrue(
            self.permission.has_object_permission(
                request_for(admin), None, recommendation
            )
        )
