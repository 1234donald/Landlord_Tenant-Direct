"""
Unit tests for Phase 7, Sprint 7.1 - Apartment serializers.

These construct the DRF serializers directly and assert field validation
(rental price, bedroom/bathroom counts, image upload rules), landlord ownership
injection on create, partial-update behaviour and the read representations
(nested images, landlord_email source) without the HTTP layer
(SYSTEM_REQUIREMENTS 41, AGENTS 23, 24).
"""
import io

import django.test as django_tests
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.apartments.models import Apartment, ApartmentImage
from apps.apartments.serializers import (
    ApartmentCreateSerializer,
    ApartmentImageRequestSerializer,
    ApartmentImageSerializer,
    ApartmentSerializer,
    ApartmentUpdateSerializer,
)

User = get_user_model()
PASSWORD = "StrongPass123!"


def make_landlord():
    return User.objects.create_user(
        email="landlord@example.com",
        password=PASSWORD,
        full_name="Landlord User",
        role=User.Role.LANDLORD,
    )


def make_image_bytes(name="photo.png", size=(32, 32), color=(255, 0, 0)):
    buffer = io.BytesIO()
    with Image.new("RGB", size, color) as img:
        img.save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/png")


def valid_payload(**overrides):
    payload = {
        "title": "Sunny Flat",
        "description": "A bright flat.",
        "location": "Calabar",
        "address": "10 Ikot Ansa Road",
        "rental_price": "250000.00",
        "apartment_type": Apartment.ApartmentType.TWO_BEDROOM,
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


class ApartmentWriteSerializerTests(django_tests.TestCase):
    """Shared validation on the create/update apartment serializers."""

    def setUp(self):
        self.landlord = make_landlord()
        self.request_data = {"request": type("R", (), {"user": self.landlord})()}

    def test_valid_create_data_is_accepted(self):
        serializer = ApartmentCreateSerializer(
            data=valid_payload(), context=self.request_data
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_negative_rental_price_is_rejected(self):
        for cls in (ApartmentCreateSerializer, ApartmentUpdateSerializer):
            with self.subTest(cls=cls.__name__):
                serializer = cls(
                    data=valid_payload(rental_price="-1"),
                    context=self.request_data,
                )
                self.assertFalse(serializer.is_valid())
                self.assertIn("rental_price", serializer.errors)

    def test_zero_bedrooms_is_rejected(self):
        serializer = ApartmentCreateSerializer(
            data=valid_payload(bedrooms=0), context=self.request_data
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("bedrooms", serializer.errors)

    def test_zero_bathrooms_is_rejected(self):
        serializer = ApartmentCreateSerializer(
            data=valid_payload(bathrooms=0), context=self.request_data
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("bathrooms", serializer.errors)

    def test_missing_required_fields_are_rejected(self):
        serializer = ApartmentCreateSerializer(
            data={}, context=self.request_data
        )
        self.assertFalse(serializer.is_valid())
        for field in ("title", "location", "rental_price", "apartment_type",
                      "bedrooms", "bathrooms"):
            self.assertIn(field, serializer.errors)

    def test_create_injects_landlord_from_authenticated_user(self):
        serializer = ApartmentCreateSerializer(
            data=valid_payload(), context=self.request_data
        )
        self.assertTrue(serializer.is_valid())
        apartment = serializer.save()
        self.assertEqual(apartment.landlord, self.landlord)

    def test_landlord_is_never_accepted_from_client(self):
        other = User.objects.create_user(
            email="other@example.com",
            password=PASSWORD,
            full_name="Other",
            role=User.Role.LANDLORD,
        )
        # "landlord" is not a declared field and is ignored if supplied.
        data = valid_payload(landlord=other.pk)
        serializer = ApartmentCreateSerializer(
            data=data, context=self.request_data
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        apartment = serializer.save()
        self.assertEqual(apartment.landlord, self.landlord)

    def test_update_is_partial(self):
        apartment = Apartment.objects.create(
            landlord=self.landlord,
            **{k: v for k, v in valid_payload().items()},
        )
        serializer = ApartmentUpdateSerializer(
            apartment, data={"title": "Renamed Flat"}, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        apartment.refresh_from_db()
        self.assertEqual(apartment.title, "Renamed Flat")
        # Un-supplied fields are preserved.
        self.assertEqual(apartment.location, "Calabar")

    def test_update_cannot_change_landlord(self):
        apartment = Apartment.objects.create(
            landlord=self.landlord,
            **{k: v for k, v in valid_payload().items()},
        )
        serializer = ApartmentUpdateSerializer(
            apartment, data={"landlord": 999}, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertNotIn("landlord", serializer.validated_data)


class ApartmentImageRequestSerializerTests(django_tests.TestCase):
    """Direct validation of a single uploaded image file."""

    def setUp(self):
        self.serializer = ApartmentImageRequestSerializer()

    def test_valid_png_is_accepted(self):
        file_obj = make_image_bytes()
        self.assertIsNotNone(self.serializer.validate_image_file(file_obj))

    def test_none_file_is_rejected(self):
        with self.assertRaises(Exception):
            self.serializer.validate_image_file(None)

    def test_non_image_payload_is_rejected(self):
        bad = SimpleUploadedFile(
            "fake.jpg", b"not really an image", content_type="image/jpeg"
        )
        with self.assertRaises(Exception):
            self.serializer.validate_image_file(bad)


class ApartmentReadSerializerTests(django_tests.TestCase):
    def setUp(self):
        self.landlord = make_landlord()
        self.apartment = Apartment.objects.create(
            landlord=self.landlord, **valid_payload()
        )
        self.image = ApartmentImage.objects.create(
            apartment=self.apartment, image="apartments/pic.jpg"
        )

    def test_serializer_includes_landlord_email_source(self):
        data = ApartmentSerializer(self.apartment).data
        self.assertEqual(data["landlord_email"], self.landlord.email)
        self.assertEqual(data["landlord"], self.landlord.pk)

    def test_serializer_nests_images(self):
        data = ApartmentSerializer(self.apartment).data
        self.assertEqual(len(data["images"]), 1)
        self.assertEqual(data["images"][0]["id"], self.image.pk)
        self.assertIn("image", data["images"][0])

    def test_image_read_serializer_fields_are_read_only(self):
        serializer = ApartmentImageSerializer(self.image)
        for field in ("id", "image", "order", "uploaded_at"):
            self.assertTrue(serializer.fields[field].read_only)

    def test_apartment_read_fields_are_read_only(self):
        serializer = ApartmentSerializer(self.apartment)
        for field in ("rental_price", "bedrooms", "bathrooms", "images"):
            self.assertTrue(serializer.fields[field].read_only)
