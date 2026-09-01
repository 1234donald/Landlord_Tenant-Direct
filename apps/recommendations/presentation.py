"""HTML presentation views for the Recommendation module (Phase 5, Sprint 5.6).

Provides the tenant-facing recommendation results page (AGENTS 43): it shows the
tenant's most recent persisted ``Recommendation`` run ranked by preference
match, and lets the tenant regenerate recommendations from their latest stored
preference. Terminology stays factual ("Recommended for you", "Similarity
score") and never claims a guaranteed best property.
"""
from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from apps.apartments.models import Apartment

from apps.recommendations.models import Preference, Recommendation
from apps.recommendations.services import NoPreferenceError, generate_recommendations


class PreferenceForm(forms.ModelForm):
    """Tenant preference form mirroring the API preference validation.

    ``max_rent`` must be positive, bedroom/bathroom counts numeric and positive,
    and the apartment type is one of the ``Apartment`` choices (AGENTS 10, 23).
    """

    class Meta:
        model = Preference
        exclude = ["tenant", "created_at", "updated_at"]
        widgets = {
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "max_rent": forms.NumberInput(attrs={"class": "form-control", "min": "0", "step": "0.01"}),
            "apartment_type": forms.Select(attrs={"class": "form-select"}),
            "bedrooms": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "bathrooms": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "additional_facilities": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean_max_rent(self):
        value = self.cleaned_data["max_rent"]
        if value is not None and value < 0:
            raise forms.ValidationError(
                "Maximum rental price must be a positive number."
            )
        return value

    def clean_bedrooms(self):
        value = self.cleaned_data["bedrooms"]
        if value is not None and value <= 0:
            raise forms.ValidationError("Bedroom count must be at least 1.")
        return value

    def clean_bathrooms(self):
        value = self.cleaned_data["bathrooms"]
        if value is not None and value <= 0:
            raise forms.ValidationError("Bathroom count must be at least 1.")
        return value


class PreferenceFormPageView(LoginRequiredMixin, View):
    """Tenant-only page to create or update their apartment preferences.

    Uses the tenant's latest stored preference as the initial form data, so
    editing a preference never creates a confusing duplicate row. Validation and
    saving happen server-side.
    """

    template_name = "recommendations/preference_form.html"
    http_method_names = ["get", "post"]

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated and not (user.is_tenant or user.is_admin):
            return HttpResponseForbidden("Forbidden")
        return super().dispatch(request, *args, **kwargs)

    def _get_instance(self, user):
        return Preference.objects.filter(tenant=user).first()

    def get(self, request, *args, **kwargs):
        form = PreferenceForm(instance=self._get_instance(request.user))
        return render(
            request,
            self.template_name,
            {"form": form, "apartment_types": Apartment.ApartmentType.choices},
        )

    def post(self, request, *args, **kwargs):
        user = request.user
        instance = self._get_instance(user)
        form = PreferenceForm(request.POST, instance=instance)
        if form.is_valid():
            preference = form.save(commit=False)
            preference.tenant = user
            preference.save()
            messages.success(request, "Your preferences have been saved.")
            return redirect("recent-recommendations")
        return render(
            request,
            self.template_name,
            {"form": form, "apartment_types": Apartment.ApartmentType.choices},
            status=400,
        )


class RecommendationResultsPageView(LoginRequiredMixin, TemplateView):
    """Tenant-only page showing the latest recommendation run.

    ``GET`` renders the most recent run (or a helpful empty state when none
    exists or the tenant has no stored preference). ``POST`` regenerates
    recommendations from the tenant's latest preference and redirects back.
    """

    template_name = "recommendations/results.html"

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated and not (user.is_tenant or user.is_admin):
            return HttpResponseForbidden("Forbidden")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        user = request.user
        try:
            preference = Preference.objects.filter(tenant=user).first()
            if preference is None:
                raise NoPreferenceError(
                    "Save an apartment preference first so we can recommend homes."
                )
            generate_recommendations(user, preference)
        except NoPreferenceError:
            pass
        return redirect(reverse("recommendation-results"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        recommendation = (
            Recommendation.objects.filter(
                tenant=user,
                items__isnull=False,
            )
            .prefetch_related("items__apartment__images")
            .first()
        )
        context["recommendation"] = recommendation
        context["has_preference"] = Preference.objects.filter(tenant=user).exists()
        return context