from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import (
    TokenBlacklistSerializer,
    TokenRefreshSerializer,
)

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
