"""Views for the landlord verification workflow (Phase 3, Sprint 3.2).

Implements the Verification API (§24.6):
- ``POST /api/v1/verification/submit/``  landlord submission
- ``GET  /api/v1/verification/status/``   landlord sees their status
- ``GET  /api/v1/admin/verifications/``   admin listing
- ``POST /api/v1/admin/verifications/{id}/approve/``
- ``POST /api/v1/admin/verifications/{id}/reject/``

Role enforcement: submission/status require the LANDLORD role; the review
listing and approve/reject actions require the ADMIN role. A landlord can
never review their own request because review actions are admin-only.
"""
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdmin, IsLandlord
from apps.core.api import paginated_payload

from .models import VerificationRequest
from .serializers import (
    VerificationRequestSerializer,
    VerificationReviewSerializer,
    VerificationSubmitSerializer,
)


class VerificationSubmitView(APIView):
    """Allow a landlord to submit verification information."""

    permission_classes = [IsLandlord]

    def post(self, request):
        serializer = VerificationSubmitSerializer(
            data=request.data,
            context={"request": request},
        )
        if serializer.is_valid():
            verification = serializer.save()
            return Response(
                {
                    "success": True,
                    "message": "Verification submitted.",
                    "data": VerificationRequestSerializer(verification).data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {
                "success": False,
                "message": "Verification submission failed.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class VerificationStatusView(APIView):
    """Return the authenticated landlord's own verification requests."""

    permission_classes = [IsLandlord]

    def get(self, request):
        requests = VerificationRequest.objects.filter(landlord=request.user)
        serializer = VerificationRequestSerializer(requests, many=True)
        return Response(
            {
                "success": True,
                "message": "Verification status retrieved.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class AdminVerificationListView(generics.ListAPIView):
    """Administrator listing of all verification requests."""

    permission_classes = [IsAdmin]
    serializer_class = VerificationRequestSerializer

    def get_queryset(self):
        queryset = VerificationRequest.objects.all()
        requested_status = self.request.query_params.get("status")
        if requested_status:
            queryset = queryset.filter(status=requested_status)
        return queryset

    def list(self, request, *args, **kwargs):
        requested_status = request.query_params.get("status")
        if requested_status:
            allowed = {choice[0] for choice in VerificationRequest.Status.choices}
            if requested_status not in allowed:
                return Response(
                    {
                        "success": False,
                        "message": "Invalid verification status filter.",
                        "errors": {"status": "Unknown status."},
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        queryset = self.filter_queryset(self.get_queryset())
        return Response(
            paginated_payload(
                request,
                queryset,
                self.get_serializer_class(),
                message="Verification requests retrieved.",
            ),
            status=status.HTTP_200_OK,
        )


class AdminVerificationApproveView(APIView):
    """Administrator approval of a pending verification request."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        verification = get_object_or_404(VerificationRequest, pk=pk)
        if not verification.is_pending:
            return Response(
                {
                    "success": False,
                    "message": "Only pending requests can be approved.",
                    "errors": {},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        verification.approve(admin=request.user)
        return Response(
            {
                "success": True,
                "message": "Verification approved.",
                "data": VerificationRequestSerializer(verification).data,
            },
            status=status.HTTP_200_OK,
        )


class AdminVerificationRejectView(APIView):
    """Administrator rejection of a pending verification request."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        verification = get_object_or_404(VerificationRequest, pk=pk)
        review_serializer = VerificationReviewSerializer(data=request.data)
        if not review_serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Verification rejection failed.",
                    "errors": review_serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not verification.is_pending:
            return Response(
                {
                    "success": False,
                    "message": "Only pending requests can be rejected.",
                    "errors": {},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        verification.reject(
            admin=request.user,
            remarks=review_serializer.validated_data.get("remarks", ""),
        )
        return Response(
            {
                "success": True,
                "message": "Verification rejected.",
                "data": VerificationRequestSerializer(verification).data,
            },
            status=status.HTTP_200_OK,
        )