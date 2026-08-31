"""
Unit tests for Phase 7, Sprint 7.1 - ApartmentImage model.

This module adds direct unit coverage for the ``ApartmentImage`` model, which
was previously exercised only incidentally through presentation tests. It
verifies the apartment relationship, the image/order fields, string
representation, Meta ordering and the declared index (SYSTEM_REQUIREMENTS 41).
"""
import django.test as django_tests
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from apps.apartments.models import Apartment, ApartmentImage

User = get_user_model()
PASSWORD = "StrongPass123!"


def make_landlord():
    return User.objects.create_user(
        email="landlord@example.com",
        password=PASSWORD,
        full_name="Landlord User",
        role=User.Role.LANDLORD,
    )


def make_apartment(landlord, **overrides):
    defaults = dict(
        landlord=landlord,
        title="Flat",
        location="Calabar",
        rental_price="250000.00",
        apartment_type=Apartment.ApartmentType.TWO_BEDROOM,
        bedrooms=2,
        bathrooms=2,
    )
    defaults.update(overrides)
    return Apartment.objects.create(**defaults)


class ApartmentImageModelTests(django_tests.TestCase):
    def setUp(self):
        self.landlord = make_landlord()
        self.apartment = make_apartment(self.landlord)

    def test_image_requires_apartment(self):
        with self.assertRaises(IntegrityError):
            ApartmentImage.objects.create(image="apartments/pic.jpg")

    def test_apartment_relationship_and_reverse(self):
        image = ApartmentImage.objects.create(
            apartment=self.apartment,
            image="apartments/pic.jpg",
        )
        self.assertEqual(image.apartment, self.apartment)
        self.assertIn(image, self.apartment.images.all())

    def test_cascade_deletion_with_apartment(self):
        image = ApartmentImage.objects.create(
            apartment=self.apartment, image="apartments/pic.jpg"
        )
        pk = image.pk
        self.apartment.delete()
        self.assertFalse(ApartmentImage.objects.filter(pk=pk).exists())

    def test_order_defaults_to_zero(self):
        image = ApartmentImage.objects.create(
            apartment=self.apartment, image="apartments/pic.jpg"
        )
        self.assertEqual(image.order, 0)

    def test_uploaded_at_populated_automatically(self):
        image = ApartmentImage.objects.create(
            apartment=self.apartment, image="apartments/pic.jpg"
        )
        self.assertIsNotNone(image.uploaded_at)

    def test_string_representation(self):
        image = ApartmentImage.objects.create(
            apartment=self.apartment, image="apartments/pic.jpg"
        )
        self.assertIn("Image for", str(image))

    def test_meta_ordering_by_order_then_id(self):
        first = ApartmentImage.objects.create(
            apartment=self.apartment, image="apartments/a.jpg", order=2
        )
        second = ApartmentImage.objects.create(
            apartment=self.apartment, image="apartments/b.jpg", order=1
        )
        self.assertEqual(
            list(ApartmentImage.objects.all()), [second, first]
        )

    def test_declared_index_on_apartment(self):
        index_names = {
            index.fields[0]
            for index in ApartmentImage._meta.indexes
        }
        self.assertIn("apartment", index_names)
