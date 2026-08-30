"""HTML presentation views for the Recommendation module (Phase 5, Sprint 5.6).

Provides the tenant-facing recommendation results page (AGENTS 43): it shows the
tenant's most recent persisted ``Recommendation`` run ranked by preference
match, and lets the tenant regenerate recommendations from their latest stored
preference. Terminology stays factual ("Recommended for you", "Similarity
score") and never claims a guaranteed best property.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from apps.recommendations.models import Preference, Recommendation
from apps.recommendations.services import NoPreferenceError, generate_recommendations


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