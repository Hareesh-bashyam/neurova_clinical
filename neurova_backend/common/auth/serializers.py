from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed


class AppTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Generates JWT tokens + validated organization context
    """

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        # ---- HARD REQUIREMENTS ----
        if not hasattr(user, "profile"):
            raise AuthenticationFailed("User profile not found")

        profile = user.profile

        if not profile.organization:
            raise AuthenticationFailed("User is not assigned to an organization")

        organization = profile.organization

        return {
            "access_token": data["access"],
            "refresh_token": data["refresh"],
            "expires_in": 3600,
            "org_id": str(organization.external_id),
            "role": profile.role,
        }
