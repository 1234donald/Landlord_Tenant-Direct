"""
Unit tests for Phase 3, Sprint 3.3 - Apartment Data Model.

These verify the ``Apartment`` listing model: the landlord relationship,
listing attributes, facility availability, furnishing and availability status,
validation rules and database indexes. They require a test database.
"""
import django.test as django_tests
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.apartments.models import Apartment

User = get_user_model()

PASSWORD = "StrongPass123!"


def make_landlord(email="landlord@example.com"):
    return User.objects.create_user(
        email=email,
        password=PASSWORD,
        full_name="Landlord User",
        role=User.Role.LANDLORD,
    )


def make_apartment(landlord=None, **kwargs):
    defaults = {
        "title": "Sunny 2-Bedroom Flat",
        "description": "A bright two-bedroom flat near town.",
        "location": "Calabar",
        "address": "10 Ikot Ansa Road",
        "rental_price": "250000.00",
        "apartment_type": Apartment.ApartmentType.TWO_BEDROOM,
        "bedrooms": 2,
        "bathrooms": 2,
        "availability": True,
    }
    defaults.update(kwargs)
    return Apartment.objects.create(landlord=landlord or make_landlord(), **defaults)


class ApartmentModelTests(django_tests.TestCase):
    def test_landlord_relationship(self):
        landlord = make_landlord()
        apartment = make_apartment(landlord=landlord)
        self.assertEqual(apartment.landlord, landlord)
        self.assertIn(apartment, landlord.apartments.all())

    def test_apartment_requires_a_landlord(self):
        with self.assertRaises(Exception):
            Apartment.objects.create(
                title="No Landlord",
                location="Calabar",
                rental_price="100000.00",
                apartment_type=Apartment.ApartmentType.FLAT,
                bedrooms=1,
                bathrooms=1,
            )

    def test_listing_attributes_are_stored(self):
        apartment = make_apartment(
            title="Cozy Self-contained",
            description="A cozy unit.",
            location="Uyo",
            address="12 Udo Street",
            rental_price="120000.00",
            apartment_type=Apartment.ApartmentType.SELF_CONTAINED,
            bedrooms=1,
            bathrooms=1,
        )
        self.assertEqual(apartment.title, "Cozy Self-contained")
        self.assertEqual(apartment.location, "Uyo")
        self.assertEqual(str(apartment.rental_price), "120000.00")
        self.assertEqual(apartment.apartment_type, "SELF_CONTAINED")
        self.assertEqual(apartment.bedrooms, 1)
        self.assertEqual(apartment.bathrooms, 1)

    def test_apartment_type_choices(self):
        self.assertEqual(
            set(Apartment.ApartmentType.values),
            {
                "SELF_CONTAINED",
                "ONE_BEDROOM",
                "TWO_BEDROOM",
                "THREE_BEDROOM",
                "FLAT",
                "DUPLEX",
            },
        )

    def test_facility_flags_default_to_false(self):
        apartment = make_apartment()
        self.assertFalse(apartment.parking)
        self.assertFalse(apartment.electricity)
        self.assertFalse(apartment.water)
        self.assertFalse(apartment.security)
        self.assertFalse(apartment.furnished)
        self.assertEqual(apartment.additional_facilities, "")

    def test_facility_flags_can_be_set(self):
        apartment = make_apartment(
            parking=True,
            electricity=True,
            water=True,
            security=True,
            furnished=True,
            additional_facilities="Swimming pool, gym",
        )
        self.assertTrue(apartment.parking)
        self.assertTrue(apartment.electricity)
        self.assertTrue(apartment.water)
        self.assertTrue(apartment.security)
        self.assertTrue(apartment.furnished)
        self.assertEqual(apartment.additional_facilities, "Swimming pool, gym")

    def test_availability_defaults_to_true(self):
        apartment = make_apartment()
        self.assertTrue(apartment.availability)

    def test_availability_can_be_set_to_false(self):
        apartment = make_apartment(availability=False)
        self.assertFalse(apartment.availability)

    def test_timestamps_are_populated(self):
        apartment = make_apartment()
        self.assertIsNotNone(apartment.created_at)
        self.assertIsNotNone(apartment.updated_at)

    def test_rental_price_must_be_positive(self):
        apartment = make_apartment(rental_price="-5000.00")
        with self.assertRaises(ValidationError):
            apartment.full_clean()

    def test_bedroom_count_must_be_at_least_one(self):
        apartment = make_apartment(bedrooms=0)
        with self.assertRaises(ValidationError):
            apartment.full_clean()

    def test_bathroom_count_must_be_at_least_one(self):
        apartment = make_apartment(bathrooms=0)
        with self.assertRaises(ValidationError):
            apartment.full_clean()

    def test_valid_apartment_passes_validation(self):
        apartment = make_apartment()
        try:
            apartment.full_clean()
        except ValidationError:
            self.fail("A valid apartment must pass full_clean().")

    def test_string_representation_is_title(self):
        apartment = make_apartment(title="Greenview Apartment")
        self.assertEqual(str(apartment), "Greenview Apartment")

    def test_default_ordering_newest_first(self):
        landlord = make_landlord()
        a = make_apartment(landlord=landlord, title="First")
        b = make_apartment(landlord=landlord, title="Second")
        self.assertEqual(
            list(Apartment.objects.all()),
            [b, a],
        )

    def test_required_query_fields_are_indexed(self):
        indexed_fields = {
            index.fields[0]
            for index in Apartment._meta.indexes
        }
        for field in ("location", "rental_price", "apartment_type",
                      "landlord", "availability"):
            self.assertIn(field, indexed_fields)
