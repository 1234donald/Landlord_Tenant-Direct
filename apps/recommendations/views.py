"""Views for the Tenant Preference module (Phase 4, Sprint 4.4).

Implements tenant-preference management (§24.3):
- ``GET    /api/v1/preferences/``         list the authenticated tenant's preferences
- ``POST   /api/v1/preferences/``         create a preference owned by the tenant
- ``GET    /api/v1/preferences/{id}/``    retrieve a single preference
- ``PATCH  /api/v1/preferences/{id}/``    update a preference
- ``DELETE /api/v1/preferences/{id}/``    delete a preference

Role enforcement: list/create require the TENANT role; retrieve/update/delete
require ownership by the same tenant or an administrator
(``IsPreferenceOwnerOrAdmin``). A landlord or another tenant can never modify a
preference they do not own. Ownership is always the authenticated tenant and is
never client-supplied.
"""
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsTenant

from .models import Preference
from .permissions import IsPreferenceOwnerOrAdmin
from .serializers import (
    PreferenceCreateSerializer,
    PreferenceSerializer,
    PreferenceUpdateSerializer,
)


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
