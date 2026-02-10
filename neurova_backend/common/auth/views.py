from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .serializers import (
    AppTokenObtainPairSerializer,
    AppTokenRefreshSerializer,
    AppLogoutSerializer,
)
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated



class AppTokenObtainPairView(TokenObtainPairView):
    serializer_class = AppTokenObtainPairSerializer

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
                    "status": "ERROR",
                    "status_code": 401,
                    "message": "Invalid username or password",
                    "data": None,
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )


class AppTokenRefreshView(TokenRefreshView):
    serializer_class = AppTokenRefreshSerializer

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

        except (AuthenticationFailed, ValidationError):
            return Response(
                {
                    "success": False,
                    "status": "ERROR",
                    "status_code": 401,
                    "message": "Invalid or expired refresh token",
                    "data": None,
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )


class AppLogoutView(APIView):
    permission_classes = [IsAuthenticated]

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