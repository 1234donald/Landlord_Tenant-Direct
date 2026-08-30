"""
API tests for Phase 3, Sprint 3.5 - Apartment Update, Delete and Availability.

These verify the management endpoints for existing listings: listing edits,
availability updates, media replacement, listing deletion, and the ownership
restrictions that prevent any user other than the owning landlord or an
administrator from modifying a listing.
"""
import io

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.apartments.models import Apartment, ApartmentImage

User = get_user_model()

LOGIN_URL = "/api/v1/auth/login/"
APARTMENTS_URL = "/api/v1/apartments/"

PASSWORD = "StrongPass123!"


def make_image_bytes(name="photo.png", size=(32, 32), color=(255, 0, 0)):
    buffer = io.BytesIO()
    with Image.new("RGB", size, color) as img:
        img.save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/png")


def make_user(email, role):
    return User.objects.create_user(
        email=email,
        password=PASSWORD,
        full_name=f"{role} User",
        role=role,
    )


class ApartmentManageApiTests(APITestCase):
    def setUp(self):
        self.client = APIClient(HTTP_HOST="localhost")
        self.landlord = make_user("landlord@example.com", User.Role.LANDLORD)
        self.other_landlord = make_user("other@example.com", User.Role.LANDLORD)
        self.tenant = make_user("tenant@example.com", User.Role.TENANT)
        self.admin = make_user("admin@example.com", User.Role.ADMIN)

    def _auth_as(self, user):
        response = self.client.post(
            LOGIN_URL,
            {"email": user.email, "password": PASSWORD},
            format="json",
        )
        access = response.data["data"]["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def _create_apartment(self, landlord=None, **kwargs):
        defaults = {
            "title": "Sunny 2-Bedroom Flat",
            "description": "A bright two-bedroom flat.",
            "location": "Calabar",
            "address": "10 Ikot Ansa Road",
            "rental_price": "250000.00",
            "apartment_type": "TWO_BEDROOM",
            "bedrooms": 2,
            "bathrooms": 2,
            "availability": True,
        }
        defaults.update(kwargs)
        return Apartment.objects.create(
            landlord=landlord or self.landlord,
            **defaults,
        )

    def test_owner_can_update_listing(self):
        self._auth_as(self.landlord)
        apartment = self._create_apartment()
        response = self.client.patch(
            f"{APARTMENTS_URL}{apartment.pk}/",
            {"title": "Updated Title", "rental_price": "300000.00"},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        data = response.data["data"]
        self.assertEqual(data["title"], "Updated Title")
        self.assertEqual(data["rental_price"], "300000.00")

    def test_partial_update_preserves_unsupplied_fields(self):
        self._auth_as(self.landlord)
        apartment = self._create_apartment(location="Uyo")
        response = self.client.patch(
            f"{APARTMENTS_URL}{apartment.pk}/",
            {"title": "Only Title Changed"},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        self.assertEqual(data["title"], "Only Title Changed")
        self.assertEqual(data["location"], "Uyo")

    def test_owner_can_update_availability_to_false(self):
        self._auth_as(self.landlord)
        apartment = self._create_apartment()
        self.assertTrue(apartment.availability)
        response = self.client.patch(
            f"{APARTMENTS_URL}{apartment.pk}/",
            {"availability": False},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["data"]["availability"])
        apartment.refresh_from_db()
        self.assertFalse(apartment.availability)

    def test_owner_can_update_availability_to_true(self):
        self._auth_as(self.landlord)
        apartment = self._create_apartment(availability=False)
        response = self.client.patch(
            f"{APARTMENTS_URL}{apartment.pk}/",
            {"availability": True},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["data"]["availability"])

    def test_owner_can_replace_images_media(self):
        self._auth_as(self.landlord)
        apartment = self._create_apartment()
        original = ApartmentImage.objects.create(
            apartment=apartment,
            image=make_image_bytes("old.png"),
            order=0,
        )
        data = {"images": [make_image_bytes("newa.png"), make_image_bytes("newb.png")]}
        response = self.client.patch(
            f"{APARTMENTS_URL}{apartment.pk}/",
            data,
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        images = list(ApartmentImage.objects.filter(apartment=apartment))
        self.assertEqual(len(images), 2)
        self.assertEqual([img.order for img in images], [0, 1])
        self.assertNotEqual(images[0].pk, original.pk)

    def test_update_without_images_preserves_existing_images(self):
        self._auth_as(self.landlord)
        apartment = self._create_apartment()
        original = ApartmentImage.objects.create(
            apartment=apartment,
            image=make_image_bytes("keep.png"),
            order=0,
        )
        response = self.client.patch(
            f"{APARTMENTS_URL}{apartment.pk}/",
            {"title": "Changed"},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        images = list(ApartmentImage.objects.filter(apartment=apartment))
        self.assertEqual(len(images), 1)
        self.assertEqual(images[0].pk, original.pk)

    def test_owner_can_delete_listing(self):
        self._auth_as(self.landlord)
        apartment = self._create_apartment()
        ApartmentImage.objects.create(
            apartment=apartment,
            image=make_image_bytes("del.png"),
            order=0,
        )
        response = self.client.delete(
            f"{APARTMENTS_URL}{apartment.pk}/",
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertFalse(Apartment.objects.filter(pk=apartment.pk).exists())
        self.assertFalse(ApartmentImage.objects.filter(apartment=apartment).exists())

    def test_other_landlord_cannot_update(self):
        self._auth_as(self.other_landlord)
        apartment = self._create_apartment()
        response = self.client.patch(
            f"{APARTMENTS_URL}{apartment.pk}/",
            {"title": "Hijack"},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_other_landlord_cannot_delete(self):
        self._auth_as(self.other_landlord)
        apartment = self._create_apartment()
        response = self.client.delete(
            f"{APARTMENTS_URL}{apartment.pk}/",
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Apartment.objects.filter(pk=apartment.pk).exists())

    def test_tenant_cannot_update(self):
        self._auth_as(self.tenant)
        apartment = self._create_apartment()
        response = self.client.patch(
            f"{APARTMENTS_URL}{apartment.pk}/",
            {"title": "Tenant edit"},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_tenant_cannot_delete(self):
        self._auth_as(self.tenant)
        apartment = self._create_apartment()
        response = self.client.delete(
            f"{APARTMENTS_URL}{apartment.pk}/",
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_update(self):
        apartment = self._create_apartment()
        response = self.client.patch(
            f"{APARTMENTS_URL}{apartment.pk}/",
            {"title": "Anonymous"},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_anonymous_cannot_delete(self):
        apartment = self._create_apartment()
        response = self.client.delete(
            f"{APARTMENTS_URL}{apartment.pk}/",
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_update_another_landlords_listing(self):
        self._auth_as(self.admin)
        apartment = self._create_apartment()
        response = self.client.patch(
            f"{APARTMENTS_URL}{apartment.pk}/",
            {"availability": False},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["data"]["availability"])

    def test_admin_can_delete_another_landlords_listing(self):
        self._auth_as(self.admin)
        apartment = self._create_apartment()
        response = self.client.delete(
            f"{APARTMENTS_URL}{apartment.pk}/",
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Apartment.objects.filter(pk=apartment.pk).exists())

    def test_update_rejects_negative_price(self):
        self._auth_as(self.landlord)
        apartment = self._create_apartment()
        response = self.client.patch(
            f"{APARTMENTS_URL}{apartment.pk}/",
            {"rental_price": "-1.00"},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_rejects_invalid_image(self):
        self._auth_as(self.landlord)
        apartment = self._create_apartment()
        original = ApartmentImage.objects.create(
            apartment=apartment,
            image=make_image_bytes("keep.png"),
            order=0,
        )
        bad = SimpleUploadedFile(
            "fake.jpg", b"not really an image", content_type="image/jpeg"
        )
        response = self.client.patch(
            f"{APARTMENTS_URL}{apartment.pk}/",
            {"images": [bad]},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        images = list(ApartmentImage.objects.filter(apartment=apartment))
        self.assertEqual(len(images), 1)
        self.assertEqual(images[0].pk, original.pk)

    def test_update_missing_apartment_returns_404(self):
        self._auth_as(self.landlord)
        response = self.client.patch(
            f"{APARTMENTS_URL}99999/",
            {"title": "Gone"},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_missing_apartment_returns_404(self):
        self._auth_as(self.landlord)
        response = self.client.delete(
            f"{APARTMENTS_URL}99999/",
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
