"""
Integration tests for Phase 5, Sprint 5.6 - Recommendation results page.

These verify the presentation side of the integrated recommendation feature: a
tenant can reach the results page, see ranked recommendation cards after a run
has been generated, regenerate via the page form, and a landlord is blocked.
"""
from django.test import TestCase
from django.urls import reverse

from apps.apartments.models import Apartment


class RecommendationResultsPageTests(TestCase):
    def test_landlord_is_blocked_from_results_page(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        landlord = User.objects.create_user(
            email="landlord@example.com",
            password="StrongPass123!",
            full_name="Landlord",
            role=User.Role.LANDLORD,
        )
        self.client.force_login(landlord)
        response = self.client.get(reverse("recommendation-results"))
        self.assertEqual(response.status_code, 403)

    def test_tenant_without_preference_sees_guidance(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        tenant = User.objects.create_user(
            email="tenant@example.com",
            password="StrongPass123!",
            full_name="Tenant",
            role=User.Role.TENANT,
        )
        self.client.force_login(tenant)
        response = self.client.get(reverse("recommendation-results"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Save your preferences first")

    def test_generate_via_page_persists_and_renders_ranked_cards(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        tenant = User.objects.create_user(
            email="tenant@example.com",
            password="StrongPass123!",
            full_name="Tenant",
            role=User.Role.TENANT,
        )
        landlord = User.objects.create_user(
            email="landlord@example.com",
            password="StrongPass123!",
            full_name="Landlord",
            role=User.Role.LANDLORD,
        )
        Apartment.objects.create(
            landlord=landlord,
            title="Two-bedroom Flat",
            location="Calabar",
            rental_price="250000.00",
            apartment_type=Apartment.ApartmentType.TWO_BEDROOM,
            bedrooms=2,
            bathrooms=2,
        )
        from apps.recommendations.models import Preference, Recommendation

        Preference.objects.create(
            tenant=tenant,
            location="Calabar",
            max_rent="300000.00",
            apartment_type=Apartment.ApartmentType.TWO_BEDROOM,
            bedrooms=2,
            bathrooms=2,
        )
        self.client.force_login(tenant)
        response = self.client.post(reverse("recommendation-results"))
        self.assertEqual(response.status_code, 302)  # redirect back
        self.assertEqual(Recommendation.objects.count(), 1)

        page = self.client.get(reverse("recommendation-results"))
        self.assertContains(page, "Rank 1")
        self.assertContains(page, "Similarity score")
        self.assertContains(page, "Recommended for you")
        self.assertContains(page, "Two-bedroom Flat")