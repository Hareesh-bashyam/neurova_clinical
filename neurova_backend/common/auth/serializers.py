from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class AppTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Only responsible for generating tokens
    """

    def validate(self, attrs):
        data = super().validate(attrs)

        return {
            "access_token": data["access"],
            "refresh_token": data["refresh"],
            "expires_in": 3600,  # 1 hour (match SIMPLE_JWT)
        }
