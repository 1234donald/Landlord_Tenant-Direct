from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import (
    TokenBlacklistSerializer,
    TokenRefreshSerializer,
)

from apps.core.api import paginated_payload

from .permissions import IsAdmin, IsLandlord, IsOwnerOrAdmin, IsTenant
from .serializers import LoginSerializer, ProfileSerializer, RegisterSerializer


class RegisterView(APIView):
    """Register a new tenant or landlord account.

    Authentication is NOT required for registration. The endpoint accepts
    email, full name, optional phone, password and a role (TENANT or
    LANDLORD). Responses use a consistent ``success/message/data`` envelope.
    """

    # Unlike the JWT-protected API, registration is a public action.
    authentication_classes = []
    permission_classes = []
    # Public endpoint; rate-limit it to deter automated abuse (Sprint 6.4).
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "success": True,
                    "message": "Registration successful.",
                    "data": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {
                "success": False,
                "message": "Registration failed.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class LoginView(APIView):
    """Authenticate with email and password and return JWT tokens.

    Returns an access token (short-lived) and a refresh token (longer-lived)
    that can be exchanged for a new access token.
    """

    authentication_classes = []
    permission_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            return Response(
                {
                    "success": True,
                    "message": "Login successful.",
                    "data": {
                        "user": {
                            "id": user.pk,
                            "email": user.email,
                            "full_name": user.full_name,
                            "role": user.role,
                        },
                        "access": serializer.validated_data["access"],
                        "refresh": serializer.validated_data["refresh"],
                    },
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "success": False,
                "message": "Login failed.",
                "errors": serializer.errors,
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )


class RefreshView(APIView):
    """Exchange a valid refresh token for a fresh access token."""

    authentication_classes = []
    permission_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)
        is_valid = False
        errors = {}
        try:
            is_valid = serializer.is_valid()
            errors = serializer.errors
        except TokenError:
            errors = {"refresh": "Invalid or expired refresh token."}
        if is_valid:
            return Response(
                {
                    "success": True,
                    "message": "Token refreshed.",
                    "data": {"access": serializer.validated_data["access"]},
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "success": False,
                "message": "Token refresh failed.",
                "errors": errors,
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )


class LogoutView(APIView):
    """Revoke the provided refresh token using the blacklist.

    The refresh token submitted with the request is added to the blacklist so
    it can no longer be used to obtain access tokens.
    """

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = TokenBlacklistSerializer(data=request.data)
        is_valid = False
        errors = {}
        try:
            is_valid = serializer.is_valid()
            errors = serializer.errors
        except TokenError:
            errors = {"refresh": "Invalid or expired refresh token."}
        if is_valid:
            return Response(
                {"success": True, "message": "Logout successful.", "data": {}},
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "success": False,
                "message": "Logout failed.",
                "errors": errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class MeView(APIView):
    """Return and update the profile of the currently authenticated user.

    This endpoint requires a valid Bearer access token. ``GET`` returns the
    profile; ``PATCH`` allows the user to edit their own contact/profile
    details (``full_name`` and ``phone``).
    """

    def get(self, request):
        user = request.user
        return Response(
            {
                "success": True,
                "message": "Profile retrieved.",
                "data": {
                    "id": user.pk,
                    "email": user.email,
                    "full_name": user.full_name,
                    "phone": user.phone or "",
                    "role": user.role,
                },
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request):
        serializer = ProfileSerializer(
            request.user, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "success": True,
                    "message": "Profile updated.",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "success": False,
                "message": "Profile update failed.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class TenantAreaView(APIView):
    """Protected tenant-only endpoint.

    Demonstrates the ``IsTenant`` role permission. Returns the authenticated
    tenant's own profile. Expanded into the full tenant dashboard in later
    phases.
    """

    permission_classes = [IsTenant]

    def get(self, request):
        return Response(
            {
                "success": True,
                "message": "Tenant area accessible.",
                "data": {
                    "id": request.user.pk,
                    "email": request.user.email,
                    "full_name": request.user.full_name,
                    "phone": request.user.phone or "",
                    "role": request.user.role,
                },
            },
            status=status.HTTP_200_OK,
        )


class LandlordAreaView(APIView):
    """Protected landlord-only endpoint.

    Demonstrates the ``IsLandlord`` role permission. Returns the authenticated
    landlord's own profile. Expanded into the full landlord dashboard in later
    phases.
    """

    permission_classes = [IsLandlord]

    def get(self, request):
        return Response(
            {
                "success": True,
                "message": "Landlord area accessible.",
                "data": {
                    "id": request.user.pk,
                    "email": request.user.email,
                    "full_name": request.user.full_name,
                    "phone": request.user.phone or "",
                    "role": request.user.role,
                },
            },
            status=status.HTTP_200_OK,
        )


class UserListView(generics.ListAPIView):
    """List all registered users (administrator only).

    Backs the administrative "manage users" function. Returns real records
    from the database.
    """

    permission_classes = [IsAdmin]
    serializer_class = ProfileSerializer
    queryset = get_user_model().objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer_class = self.get_serializer_class()
        return Response(
            paginated_payload(
                request,
                queryset,
                serializer_class,
                message="Users retrieved.",
            ),
            status=status.HTTP_200_OK,
        )


class UserDetailView(generics.RetrieveAPIView):
    """View a single user's profile.

    Uses ``IsOwnerOrAdmin``: a user may view their own profile, or any
    administrator may view any profile.
    """

    permission_classes = [IsOwnerOrAdmin]
    serializer_class = ProfileSerializer

    def get_queryset(self):
        return get_user_model().objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(
            {
                "success": True,
                "message": "User retrieved.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
