from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework import serializers

User = get_user_model()


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
            "expires_in": settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].seconds,
            "org_id": str(organization.external_id),
            "role": profile.role,
        }


class AppTokenRefreshSerializer(TokenRefreshSerializer):
    """
    Refreshes access token and returns org + role context
    """

    def validate(self, attrs):
        data = super().validate(attrs)

        refresh = RefreshToken(attrs["refresh"])

        # ✅ Extract user_id from token payload (SimpleJWT way)
        user_id = refresh.payload.get("user_id")
        if not user_id:
            raise AuthenticationFailed("Invalid refresh token")

        try:
            user = (
                User.objects
                .select_related("profile", "profile__organization")
                .get(id=user_id)
            )
        except User.DoesNotExist:
            raise AuthenticationFailed("User not found")

        # ---- SAME HARD REQUIREMENTS AS LOGIN ----
        if not hasattr(user, "profile"):
            raise AuthenticationFailed("User profile not found")

        profile = user.profile

        if not profile.organization:
            raise AuthenticationFailed("User is not assigned to an organization")

        organization = profile.organization

        return {
            "access_token": data["access"],
            "refresh_token": attrs["refresh"],  # reuse existing refresh token
            "expires_in": settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].seconds,
            "org_id": str(organization.external_id),
            "role": profile.role,
        }


class AppLogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

    def validate(self, attrs):
        try:
            self.token = RefreshToken(attrs["refresh_token"])
        except Exception:
            raise AuthenticationFailed("Invalid refresh token")

        return attrs

    def save(self, **kwargs):
        # Blacklist refresh token
        self.token.blacklist()
