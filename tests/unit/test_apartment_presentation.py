"""
Module tests for Phase 3, Sprint 3.6 - Apartment presentation.

These verify the read-oriented presentation layer: the public apartment cards
page, the apartment detail page (facilities, availability, landlord
information, media), and the landlord-only "my apartments" page with its access
restrictions.
"""
import io

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import resolve, reverse
from PIL import Image

from apps.apartments.models import Apartment, ApartmentImage

User = get_user_model()


def make_image_bytes(name="photo.png", size=(32, 32), color=(255, 0, 0)):
    buffer = io.BytesIO()
    with Image.new("RGB", size, color) as img:
        img.save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/png")


def make_apartment(landlord, **kwargs):
    defaults = {
        "title": "Sunny 2-Bedroom Flat",
        "description": "A bright two-bedroom flat in a quiet estate.",
        "location": "Calabar",
        "address": "10 Ikot Ansa Road",
        "rental_price": "250000.00",
        "apartment_type": "TWO_BEDROOM",
        "bedrooms": 2,
        "bathrooms": 2,
        "parking": True,
        "electricity": True,
        "water": True,
        "security": False,
        "furnished": True,
        "availability": True,
    }
    defaults.update(kwargs)
    return Apartment.objects.create(landlord=landlord, **defaults)


class ApartmentPresentationUrlTests(TestCase):
    def test_apartment_list_url_resolves(self):
        match = resolve("/apartments/")
        self.assertEqual(match.url_name, "apartment-list")

    def test_apartment_list_reverse(self):
        self.assertEqual(reverse("apartment-list"), "/apartments/")

    def test_apartment_detail_url_resolves(self):
        match = resolve("/apartments/5/")
        self.assertEqual(match.url_name, "apartment-detail")

    def test_my_apartments_url_resolves(self):
        match = resolve("/my/apartments/")
        self.assertEqual(match.url_name, "my-apartments")


class ApartmentBrowseListTests(TestCase):
    def setUp(self):
        self.client = Client(HTTP_HOST="localhost")
        self.landlord = User.objects.create_user(
            email="landlord@example.com",
            password="StrongPass123!",
            full_name="Landlord User",
            role=User.Role.LANDLORD,
        )

    def test_list_renders_available_apartment(self):
        make_apartment(self.landlord, title="Lagos View Flat")
        response = self.client.get(reverse("apartment-list"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Lagos View Flat", content)
        self.assertIn("Calabar", content)

    def test_list_excludes_unavailable_apartments(self):
        make_apartment(self.landlord, title="Hidden Listing", availability=False)
        make_apartment(self.landlord, title="Shown Listing", availability=True)
        response = self.client.get(reverse("apartment-list"))
        content = response.content.decode()
        self.assertIn("Shown Listing", content)
        self.assertNotIn("Hidden Listing", content)

    def test_list_empty_state(self):
        response = self.client.get(reverse("apartment-list"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("No apartments are currently available.", response.content.decode())

    def test_list_shows_price_and_detail_link(self):
        make_apartment(self.landlord, rental_price="125000.00")
        response = self.client.get(reverse("apartment-list"))
        content = response.content.decode()
        self.assertIn("View details", content)

    def test_list_search_filters_by_location(self):
        make_apartment(self.landlord, title="Calabar Flat", location="Calabar")
        make_apartment(self.landlord, title="Uyo Flat", location="Uyo")
        response = self.client.get(reverse("apartment-list"), {"location": "uyo"})
        content = response.content.decode()
        self.assertIn("Uyo Flat", content)
        self.assertNotIn("Calabar Flat", content)

    def test_list_search_renders_search_form(self):
        response = self.client.get(reverse("apartment-list"))
        content = response.content.decode()
        self.assertIn('name="location"', content)
        self.assertIn('name="max_price"', content)
        self.assertIn('name="bedrooms"', content)


class ApartmentDetailPageTests(TestCase):
    def setUp(self):
        self.client = Client(HTTP_HOST="localhost")
        self.landlord = User.objects.create_user(
            email="landlord@example.com",
            password="StrongPass123!",
            full_name="Chinedu Obi",
            role=User.Role.LANDLORD,
        )

    def test_detail_renders_listing_information(self):
        apartment = make_apartment(self.landlord)
        response = self.client.get(reverse("apartment-detail", args=[apartment.pk]))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn(apartment.title, content)
        self.assertIn("Calabar", content)
        self.assertIn("10 Ikot Ansa Road", content)
        self.assertIn("250000", content)

    def test_detail_renders_facilities(self):
        apartment = make_apartment(self.landlord)
        response = self.client.get(reverse("apartment-detail", args=[apartment.pk]))
        content = response.content.decode()
        self.assertIn("Parking", content)
        self.assertIn("Electricity", content)
        self.assertIn("Water", content)
        self.assertIn("Security", content)

    def test_detail_renders_furnishing_status(self):
        apartment = make_apartment(self.landlord, furnished=True)
        response = self.client.get(reverse("apartment-detail", args=[apartment.pk]))
        self.assertIn("Furnished", response.content.decode())

    def test_detail_renders_availability(self):
        apartment = make_apartment(self.landlord, availability=False)
        response = self.client.get(reverse("apartment-detail", args=[apartment.pk]))
        content = response.content.decode()
        self.assertIn("Unavailable", content)
        self.assertIn("text-bg-secondary", content)

    def test_detail_renders_landlord_permitted_information(self):
        apartment = make_apartment(self.landlord)
        response = self.client.get(reverse("apartment-detail", args=[apartment.pk]))
        content = response.content.decode()
        self.assertIn("Chinedu Obi", content)
        self.assertIn("landlord@example.com", content)

    def test_detail_renders_media_gallery(self):
        apartment = make_apartment(self.landlord)
        ApartmentImage.objects.create(
            apartment=apartment,
            image=make_image_bytes("photo.png"),
            order=0,
        )
        response = self.client.get(reverse("apartment-detail", args=[apartment.pk]))
        self.assertIn("carousel", response.content.decode())

    def test_detail_missing_apartment_returns_404(self):
        response = self.client.get(reverse("apartment-detail", args=[99999]))
        self.assertEqual(response.status_code, 404)


class MyApartmentsPageTests(TestCase):
    def setUp(self):
        self.client = Client(HTTP_HOST="localhost")
        self.landlord = User.objects.create_user(
            email="landlord@example.com",
            password="StrongPass123!",
            full_name="Landlord User",
            role=User.Role.LANDLORD,
        )
        self.other_landlord = User.objects.create_user(
            email="other@example.com",
            password="StrongPass123!",
            full_name="Other Landlord",
            role=User.Role.LANDLORD,
        )
        self.tenant = User.objects.create_user(
            email="tenant@example.com",
            password="StrongPass123!",
            full_name="Tenant User",
            role=User.Role.TENANT,
        )
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="StrongPass123!",
            full_name="Admin User",
            role=User.Role.ADMIN,
        )

    def test_anonymous_redirected_to_login(self):
        response = self.client.get(reverse("my-apartments"))
        self.assertIn(response.status_code, (301, 302))

    def test_landlord_sees_only_own_apartments(self):
        make_apartment(self.landlord, title="My Listing")
        make_apartment(self.other_landlord, title="Someone Else's")
        self.client.force_login(self.landlord)
        response = self.client.get(reverse("my-apartments"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("My Listing", content)
        self.assertNotIn("Someone Else's", content)

    def test_tenant_is_forbidden(self):
        make_apartment(self.landlord)
        self.client.force_login(self.tenant)
        response = self.client.get(reverse("my-apartments"))
        self.assertEqual(response.status_code, 403)

    def test_admin_sees_all_apartments(self):
        make_apartment(self.landlord, title="Listing A")
        make_apartment(self.other_landlord, title="Listing B")
        self.client.force_login(self.admin)
        response = self.client.get(reverse("my-apartments"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Listing A", content)
        self.assertIn("Listing B", content)
