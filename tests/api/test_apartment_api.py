"""
API tests for Phase 3, Sprint 3.4 - Apartment Creation and Media.

These verify the landlord-only apartment creation endpoint, the listing and
image validation rules, image upload handling and the ownership assignment.
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


def make_video_bytes(name="tour.mp4"):
    # Minimal MP4 signature: bytes 4-7 hold the "ftyp" brand.
    return SimpleUploadedFile(
        name,
        b"\x00\x00\x00\x20ftypmp42" + b"\x00" * (4096 - 12),
        content_type="video/mp4",
    )


def make_landlord(email="landlord@example.com"):
    return User.objects.create_user(
        email=email,
        password=PASSWORD,
        full_name="Landlord User",
        role=User.Role.LANDLORD,
    )


def make_tenant(email="tenant@example.com"):
    return User.objects.create_user(
        email=email,
        password=PASSWORD,
        full_name="Tenant User",
        role=User.Role.TENANT,
    )


def make_admin(email="admin@example.com"):
    return User.objects.create_user(
        email=email,
        password=PASSWORD,
        full_name="Admin User",
        role=User.Role.ADMIN,
    )


def valid_payload(**overrides):
    payload = {
        "title": "Sunny 2-Bedroom Flat",
        "description": "A bright two-bedroom flat near town.",
        "location": "Calabar",
        "address": "10 Ikot Ansa Road",
        "rental_price": "250000.00",
        "apartment_type": "TWO_BEDROOM",
        "bedrooms": 2,
        "bathrooms": 2,
        "parking": True,
        "electricity": True,
        "water": True,
        "security": True,
        "furnished": False,
        "additional_facilities": "",
        "availability": True,
    }
    payload.update(overrides)
    return payload


class ApartmentCreateApiTests(APITestCase):
    def setUp(self):
        self.client = APIClient(HTTP_HOST="localhost")
        self.landlord = make_landlord()
        self.tenant = make_tenant()
        self.admin = make_admin()

    def _auth_as(self, user):
        response = self.client.post(
            LOGIN_URL,
            {"email": user.email, "password": PASSWORD},
            format="json",
        )
        access = response.data["data"]["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def test_landlord_can_create_apartment(self):
        self._auth_as(self.landlord)
        response = self.client.post(
            APARTMENTS_URL,
            valid_payload(),
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        data = response.data["data"]
        self.assertEqual(data["title"], "Sunny 2-Bedroom Flat")
        self.assertEqual(data["landlord"], self.landlord.pk)

    def test_landlord_ownership_is_assigned_to_authenticated_user(self):
        self._auth_as(self.landlord)
        other = make_landlord(email="other@example.com")
        response = self.client.post(
            APARTMENTS_URL,
            valid_payload(title="Owned by requesting landlord"),
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        apartment = Apartment.objects.get(pk=response.data["data"]["id"])
        self.assertEqual(apartment.landlord, self.landlord)
        self.assertNotEqual(apartment.landlord, other)
        self.assertIn(apartment, self.landlord.apartments.all())

    def test_tenant_cannot_create_apartment(self):
        self._auth_as(self.tenant)
        response = self.client.post(
            APARTMENTS_URL,
            valid_payload(),
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_cannot_create_apartment(self):
        self._auth_as(self.admin)
        response = self.client.post(
            APARTMENTS_URL,
            valid_payload(),
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_create_apartment(self):
        response = self.client.post(
            APARTMENTS_URL,
            valid_payload(),
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_creation_requires_required_fields(self):
        self._auth_as(self.landlord)
        response = self.client.post(
            APARTMENTS_URL,
            {"title": "Missing everything else"},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("location", response.data["errors"])
        self.assertIn("rental_price", response.data["errors"])
        self.assertIn("apartment_type", response.data["errors"])
        self.assertIn("bedrooms", response.data["errors"])
        self.assertIn("bathrooms", response.data["errors"])

    def test_creation_rejects_negative_price(self):
        self._auth_as(self.landlord)
        response = self.client.post(
            APARTMENTS_URL,
            valid_payload(rental_price="-100.00"),
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("rental_price", response.data["errors"])

    def test_creation_rejects_zero_bedrooms(self):
        self._auth_as(self.landlord)
        response = self.client.post(
            APARTMENTS_URL,
            valid_payload(bedrooms=0),
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_creation_rejects_invalid_apartment_type(self):
        self._auth_as(self.landlord)
        response = self.client.post(
            APARTMENTS_URL,
            valid_payload(apartment_type="BUNGALOW"),
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("apartment_type", response.data["errors"])

    def test_landlord_can_create_apartment_with_images(self):
        self._auth_as(self.landlord)
        data = valid_payload()
        data["images"] = [make_image_bytes("a.png"), make_image_bytes("b.png")]
        response = self.client.post(
            APARTMENTS_URL,
            data,
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        apartment_id = response.data["data"]["id"]
        apartment = Apartment.objects.get(pk=apartment_id)
        images = list(ApartmentImage.objects.filter(apartment=apartment))
        self.assertEqual(len(images), 2)
        self.assertEqual([img.order for img in images], [0, 1])

    def test_creation_rejects_unsupported_image_type(self):
        self._auth_as(self.landlord)
        bad = SimpleUploadedFile(
            "document.pdf", b"%PDF-1.4 fake", content_type="application/pdf"
        )
        data = valid_payload()
        data["images"] = [bad]
        response = self.client.post(
            APARTMENTS_URL,
            data,
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("images", response.data["errors"])
        self.assertEqual(Apartment.objects.count(), 0)

    def test_creation_rejects_oversized_image(self):
        self._auth_as(self.landlord)
        # Build an image that exceeds the 5 MB limit.
        big = SimpleUploadedFile(
            "big.png",
            b"\x00" * (6 * 1024 * 1024),
            content_type="image/png",
        )
        data = valid_payload()
        data["images"] = [big]
        response = self.client.post(
            APARTMENTS_URL,
            data,
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("images", response.data["errors"])
        self.assertEqual(Apartment.objects.count(), 0)

    def test_creation_does_not_persist_apartment_when_image_invalid(self):
        self._auth_as(self.landlord)
        bad = SimpleUploadedFile(
            "fake.jpg", b"not really an image", content_type="image/jpeg"
        )
        data = valid_payload()
        data["images"] = [bad]
        response = self.client.post(
            APARTMENTS_URL,
            data,
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Apartment.objects.count(), 0)
        self.assertEqual(ApartmentImage.objects.count(), 0)

    def test_creation_without_images_has_empty_list(self):
        self._auth_as(self.landlord)
        response = self.client.post(
            APARTMENTS_URL,
            valid_payload(),
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["images"], [])

    def test_landlord_can_create_apartment_with_video(self):
        self._auth_as(self.landlord)
        data = valid_payload()
        data["video"] = make_video_bytes()
        response = self.client.post(
            APARTMENTS_URL,
            data,
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        apartment = Apartment.objects.get(pk=response.data["data"]["id"])
        self.assertTrue(apartment.video.name.endswith(".mp4"))

    def test_creation_rejects_unsupported_video_type(self):
        self._auth_as(self.landlord)
        bad = SimpleUploadedFile(
            "tour.avi",
            b"\x00\x00\x00\x20ftypmp42" + b"\x00" * 1024,
            content_type="video/x-msvideo",
        )
        data = valid_payload()
        data["video"] = bad
        response = self.client.post(
            APARTMENTS_URL,
            data,
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("video", response.data["errors"])
        self.assertEqual(Apartment.objects.count(), 0)

    def test_creation_rejects_fake_video_content(self):
        self._auth_as(self.landlord)
        bad = SimpleUploadedFile(
            "tour.mp4", b"not really a video", content_type="video/mp4"
        )
        data = valid_payload()
        data["video"] = bad
        response = self.client.post(
            APARTMENTS_URL,
            data,
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("video", response.data["errors"])
        self.assertEqual(Apartment.objects.count(), 0)

    def test_creation_rejects_oversized_video(self):
        self._auth_as(self.landlord)
        big = SimpleUploadedFile(
            "big.mp4",
            b"\x00\x00\x00\x20ftypmp42" + b"\x00" * (51 * 1024 * 1024),
            content_type="video/mp4",
        )
        data = valid_payload()
        data["video"] = big
        response = self.client.post(
            APARTMENTS_URL,
            data,
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("video", response.data["errors"])
        self.assertEqual(Apartment.objects.count(), 0)
