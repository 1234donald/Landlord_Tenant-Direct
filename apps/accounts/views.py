from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RegisterSerializer


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
