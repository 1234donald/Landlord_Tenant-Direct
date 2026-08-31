"""
API tests for Phase 3, Sprint 3.2 - Verification Workflow.

These verify the Verification API (§24.6): landlord submission and status,
the administrative review listing, and the approve/reject actions, including
the role-based access control around each endpoint.
"""
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.verification.models import VerificationRequest

User = get_user_model()

LOGIN_URL = "/api/v1/auth/login/"
SUBMIT_URL = "/api/v1/verification/submit/"
STATUS_URL = "/api/v1/verification/status/"
ADMIN_LIST_URL = "/api/v1/admin/verifications/"

PASSWORD = "StrongPass123!"


class VerificationApiTests(APITestCase):
    def setUp(self):
        self.client = APIClient(HTTP_HOST="localhost")
        self.landlord = User.objects.create_user(
            email="landlord@example.com",
            password=PASSWORD,
            full_name="Landlord User",
            role=User.Role.LANDLORD,
        )
        self.tenant = User.objects.create_user(
            email="tenant@example.com",
            password=PASSWORD,
            full_name="Tenant User",
            role=User.Role.TENANT,
        )
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password=PASSWORD,
            full_name="Admin User",
            role=User.Role.ADMIN,
        )

    def _auth_as(self, user):
        response = self.client.post(
            LOGIN_URL,
            {"email": user.email, "password": PASSWORD},
            format="json",
        )
        access = response.data["data"]["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def _create_request(self, landlord=None, status_=VerificationRequest.Status.PENDING):
        return VerificationRequest.objects.create(
            landlord=landlord or self.landlord,
            information="Landlord identification and address details.",
            status=status_,
        )

    def test_landlord_can_submit_verification(self):
        self._auth_as(self.landlord)
        response = self.client.post(
            SUBMIT_URL,
            {"information": "ID, address reference and contact details."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        data = response.data["data"]
        self.assertEqual(data["status"], "PENDING")
        self.assertEqual(data["landlord"], self.landlord.pk)

    def test_submission_rejects_blank_information(self):
        self._auth_as(self.landlord)
        response = self.client.post(
            SUBMIT_URL,
            {"information": "   "},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_landlord_cannot_submit_twice_while_pending(self):
        self._auth_as(self.landlord)
        self._create_request()
        response = self.client.post(
            SUBMIT_URL,
            {"information": "Another submission while pending."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("pending", str(response.data["errors"]).lower())

    def test_tenant_cannot_submit_verification(self):
        self._auth_as(self.tenant)
        response = self.client.post(
            SUBMIT_URL,
            {"information": "Not a landlord."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_cannot_submit_verification(self):
        self._auth_as(self.admin)
        response = self.client.post(
            SUBMIT_URL,
            {"information": "Admins do not submit."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_landlord_can_view_own_status(self):
        self._auth_as(self.landlord)
        self._create_request()
        response = self.client.get(STATUS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["landlord"], self.landlord.pk)

    def test_tenant_cannot_view_status(self):
        self._auth_as(self.tenant)
        response = self.client.get(STATUS_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_list_all_verifications(self):
        self._auth_as(self.admin)
        self._create_request()
        response = self.client.get(ADMIN_LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 1)

    def test_admin_verification_list_is_paginated(self):
        second_landlord = User.objects.create_user(
            email="otherlandlord@example.com",
            password=PASSWORD,
            full_name="Other Landlord",
            role=User.Role.LANDLORD,
        )
        self._create_request(landlord=self.landlord)
        self._create_request(landlord=second_landlord)
        self._auth_as(self.admin)
        response = self.client.get(ADMIN_LIST_URL, {"page": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.data["page"], 1)
        self.assertEqual(response.data["pages"], 1)
        self.assertIsNone(response.data["next"])
        self.assertIsNone(response.data["previous"])
        self.assertEqual(len(response.data["data"]), 2)

    def test_admin_list_filters_by_status(self):
        self._auth_as(self.admin)
        self._create_request(status_=VerificationRequest.Status.PENDING)
        self._create_request(status_=VerificationRequest.Status.APPROVED)
        response = self.client.get(ADMIN_LIST_URL, {"status": "APPROVED"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.data["data"]:
            self.assertEqual(item["status"], "APPROVED")

    def test_admin_list_rejects_invalid_status_filter(self):
        self._auth_as(self.admin)
        response = self.client.get(ADMIN_LIST_URL, {"status": "BOGUS"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_landlord_cannot_access_admin_list(self):
        self._auth_as(self.landlord)
        response = self.client.get(ADMIN_LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_tenant_cannot_access_admin_list(self):
        self._auth_as(self.tenant)
        response = self.client.get(ADMIN_LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_approve_pending_request(self):
        self._auth_as(self.admin)
        request_obj = self._create_request()
        response = self.client.post(
            f"{ADMIN_LIST_URL}{request_obj.pk}/approve/", {}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        data = response.data["data"]
        self.assertEqual(data["status"], "APPROVED")
        self.assertEqual(data["reviewed_by"], self.admin.pk)
        self.assertIsNotNone(data["reviewed_at"])
        request_obj.refresh_from_db()
        self.assertTrue(request_obj.is_approved)

    def test_admin_can_reject_pending_request_with_remarks(self):
        self._auth_as(self.admin)
        request_obj = self._create_request()
        response = self.client.post(
            f"{ADMIN_LIST_URL}{request_obj.pk}/reject/",
            {"remarks": "Insufficient identification."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        data = response.data["data"]
        self.assertEqual(data["status"], "REJECTED")
        self.assertEqual(data["remarks"], "Insufficient identification.")
        request_obj.refresh_from_db()
        self.assertTrue(request_obj.is_rejected)

    def test_cannot_approve_an_already_reviewed_request(self):
        self._auth_as(self.admin)
        request_obj = self._create_request(status_=VerificationRequest.Status.APPROVED)
        response = self.client.post(
            f"{ADMIN_LIST_URL}{request_obj.pk}/approve/", {}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_reject_an_already_reviewed_request(self):
        self._auth_as(self.admin)
        request_obj = self._create_request(status_=VerificationRequest.Status.REJECTED)
        response = self.client.post(
            f"{ADMIN_LIST_URL}{request_obj.pk}/reject/", {}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_landlord_cannot_approve_a_request(self):
        self._auth_as(self.landlord)
        request_obj = self._create_request()
        response = self.client.post(
            f"{ADMIN_LIST_URL}{request_obj.pk}/approve/", {}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_landlord_cannot_reject_a_request(self):
        self._auth_as(self.landlord)
        request_obj = self._create_request()
        response = self.client.post(
            f"{ADMIN_LIST_URL}{request_obj.pk}/reject/", {}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_approval_of_missing_request_returns_404(self):
        self._auth_as(self.admin)
        response = self.client.post(
            f"{ADMIN_LIST_URL}99999/approve/", {}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)