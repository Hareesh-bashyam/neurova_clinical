# common/auth/views.py

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import (
    AppTokenObtainPairSerializer,
    AppTokenRefreshSerializer,
    AppLogoutSerializer,
)
from common.encryption_decorators import decrypt_request, encrypt_response

# ==============================
# LOGIN VIEW
# ==============================

class AppTokenObtainPairView(TokenObtainPairView):
    serializer_class = AppTokenObtainPairSerializer
    permission_classes = [AllowAny]

    @decrypt_request
    @encrypt_response
    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            return Response(
                {
                    "success": True,
                    "message": "Login successful",
                    "data": serializer.validated_data,
                },
                status=status.HTTP_200_OK,
            )

        except (AuthenticationFailed, ValidationError):
            return Response(
                {
                    "success": False,
                    "message": "Invalid username or password",
                    "data": None,
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )


# ==============================
# REFRESH VIEW
# ==============================

class AppTokenRefreshView(TokenRefreshView):
    serializer_class = AppTokenRefreshSerializer
    permission_classes = [AllowAny]

    @decrypt_request
    @encrypt_response
    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            return Response(
                {
                    "success": True,
                    "message": "Token refreshed successfully",
                    "data": serializer.validated_data,
                },
                status=status.HTTP_200_OK,
            )

        except (AuthenticationFailed, ValidationError, TokenError):
            return Response(
                {
                    "success": False,
                    "message": "Invalid or expired refresh token",
                    "data": None,
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )


# ==============================
# LOGOUT VIEW (STATELESS)
# ==============================

class AppLogoutView(APIView):
    permission_classes = [AllowAny]

    @decrypt_request
    @encrypt_response
    def post(self, request):
        try:
            serializer = AppLogoutSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(
                {
                    "success": True,
                    "message": "Logged out successfully",
                    "data": None,
                },
                status=status.HTTP_200_OK,
            )

        except (AuthenticationFailed, ValidationError):
            return Response(
                {
                    "success": False,
                    "message": "Invalid or expired refresh token",
                    "data": None,
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
