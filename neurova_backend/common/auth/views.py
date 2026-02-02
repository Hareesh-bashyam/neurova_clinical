from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import AppTokenObtainPairSerializer


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
