"""Views for the Preference and Recommendation modules (Phases 4-5).

Implements tenant-preference management (§24.3):
- ``GET    /api/v1/preferences/``         list the authenticated tenant's preferences
- ``POST   /api/v1/preferences/``         create a preference owned by the tenant
- ``GET    /api/v1/preferences/{id}/``    retrieve a single preference
- ``PATCH  /api/v1/preferences/{id}/``    update a preference
- ``DELETE /api/v1/preferences/{id}/``    delete a preference

Implements the recommendation API (§24.4):
- ``POST   /api/v1/recommendations/generate/``   run and persist recommendations
- ``GET    /api/v1/recommendations/``            list the tenant's recommendations
- ``GET    /api/v1/recommendations/{id}/``       retrieve a recommendation run

Role enforcement: list/create preferrences and recommendation generation/list
require the TENANT role; preference detail requires ownership, and
recommendation detail requires the owning tenant or an administrator
(``IsRecommendationOwnerOrAdmin``). A landlord or another tenant can never read
or modify a recommendation/preference they do not own.
"""
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsTenant

from .models import Preference, Recommendation
from .permissions import (
    IsPreferenceOwnerOrAdmin,
    IsRecommendationOwnerOrAdmin,
)
from .serializers import (
    PreferenceCreateSerializer,
    PreferenceSerializer,
    PreferenceUpdateSerializer,
    RecommendationSerializer,
)
from .services import NoPreferenceError, generate_recommendations


class PreferenceListCreateView(APIView):
    """List or create the authenticated tenant's preferences.

    ``GET`` returns only the tenant's own stored preferences. ``POST`` creates a
    new preference owned by the authenticated tenant.
    """

    permission_classes = [IsTenant]

    def get(self, request):
        queryset = Preference.objects.filter(tenant=request.user)
        serializer = PreferenceSerializer(queryset, many=True)
        return Response(
            {
                "success": True,
                "message": "Preferences retrieved.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        serializer = PreferenceCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Preference creation failed.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        preference = serializer.save()
        return Response(
            {
                "success": True,
                "message": "Preference created.",
                "data": PreferenceSerializer(preference).data,
            },
            status=status.HTTP_201_CREATED,
        )


class PreferenceDetailView(APIView):
    """Retrieve, update or delete a single tenant preference.

    Access is restricted to the owning tenant or an administrator
    (``IsPreferenceOwnerOrAdmin``). Updates are partial: only the supplied
    fields are changed.
    """

    permission_classes = [IsPreferenceOwnerOrAdmin]

    def _get_owned_preference(self, request, pk):
        preference = get_object_or_404(Preference, pk=pk)
        self.check_object_permissions(request, preference)
        return preference

    def get(self, request, pk):
        preference = self._get_owned_preference(request, pk)
        return Response(
            {
                "success": True,
                "message": "Preference retrieved.",
                "data": PreferenceSerializer(preference).data,
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request, pk):
        preference = self._get_owned_preference(request, pk)
        serializer = PreferenceUpdateSerializer(
            preference,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Preference update failed.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()
        return Response(
            {
                "success": True,
                "message": "Preference updated.",
                "data": PreferenceSerializer(preference).data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        preference = self._get_owned_preference(request, pk)
        preference.delete()
        return Response(
            {
                "success": True,
                "message": "Preference deleted.",
                "data": {},
            },
            status=status.HTTP_200_OK,
        )


class _RecommendationResultsMixin:
    """Build the shared ``data`` envelope for recommendation responses."""

    @staticmethod
    def _payload(recommendation):
        serializer = RecommendationSerializer(recommendation)
        return serializer.data


class RecommendationGenerateView(_RecommendationResultsMixin, APIView):
    """Generate a recommendation run from the tenant's stored preference.

    Accepts an optional ``preference_id``; when absent, the tenant's most
    recent preferred preference is used. The Weighted KNN engine is run through
    the service layer and the resulting run persisted. Returns a 400 with a
    clear message when the tenant has no preference to recommend from.
    """

    permission_classes = [IsTenant]

    def _resolve_preference(self, request):
        preference_id = request.data.get("preference_id")
        if preference_id is not None:
            preference = get_object_or_404(Preference, pk=preference_id)
            if preference.tenant_id != request.user.id:
                raise NoPreferenceError(
                    "The preference does not belong to this tenant."
                )
            return preference
        return Preference.objects.filter(tenant=request.user).first()

    def post(self, request):
        try:
            preference = self._resolve_preference(request)
            recommendation = generate_recommendations(request.user, preference)
        except NoPreferenceError as exc:
            return Response(
                {
                    "success": False,
                    "message": str(exc),
                    "data": {},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {
                "success": True,
                "message": (
                    "Recommendations generated and saved for your preferences."
                ),
                "data": self._payload(recommendation),
            },
            status=status.HTTP_201_CREATED,
        )


class RecommendationListView(_RecommendationResultsMixin, APIView):
    """List the authenticated tenant's recommendation runs (most recent first)."""

    permission_classes = [IsTenant]

    def get(self, request):
        queryset = Recommendation.objects.filter(
            tenant=request.user
        ).prefetch_related("items__apartment__images")
        return Response(
            {
                "success": True,
                "message": "Recommendations retrieved.",
                "data": RecommendationSerializer(queryset, many=True).data,
            },
            status=status.HTTP_200_OK,
        )


class RecommendationDetailView(_RecommendationResultsMixin, APIView):
    """Retrieve a single recommendation run with its ranked items.

    Access is restricted to the owning tenant or an administrator.
    """

    permission_classes = [IsRecommendationOwnerOrAdmin]

    def get(self, request, pk):
        recommendation = get_object_or_404(
            Recommendation.objects.prefetch_related("items__apartment__images"),
            pk=pk,
        )
        self.check_object_permissions(request, recommendation)
        return Response(
            {
                "success": True,
                "message": "Recommendation retrieved.",
                "data": self._payload(recommendation),
            },
            status=status.HTTP_200_OK,
        )
