# common/auth/serializers.py

from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

User = get_user_model()


# ==============================
# LOGIN SERIALIZER
# ==============================
class AppTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Generates JWT tokens + validated organization context
    """

    def validate(self, attrs):
        try:
            data = super().validate(attrs)
        except Exception:
            raise AuthenticationFailed("Invalid username or password")

        user = self.user

        if not hasattr(user, "profile") or not user.profile.organization:
            raise AuthenticationFailed("User organization context invalid")

        profile = user.profile
        organization = profile.organization

        return {
            "access_token": data["access"],
            "refresh_token": data["refresh"],
            "expires_in": settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].seconds,
            "org_id": str(organization.external_id),
            "role": profile.role,
        }


# ==============================
# REFRESH SERIALIZER (ROTATION SAFE)
# ==============================
class AppTokenRefreshSerializer(TokenRefreshSerializer):
    """
    Secure refresh serializer with proper rotation handling
    """

    def validate(self, attrs):
        try:
            data = super().validate(attrs)
        except TokenError:
            raise AuthenticationFailed("Invalid or expired refresh token")

        # IMPORTANT:
        # When ROTATE_REFRESH_TOKENS=True,
        # super().validate() returns NEW rotated refresh token in data["refresh"]

        try:
            refresh = RefreshToken(data["refresh"])
        except TokenError:
            raise AuthenticationFailed("Invalid refresh token")

        user_id = refresh.payload.get("user_id")
        if not user_id:
            raise AuthenticationFailed("Invalid token payload")

        user = (
            User.objects
            .select_related("profile", "profile__organization")
            .filter(id=user_id)
            .first()
        )

        if not user or not hasattr(user, "profile") or not user.profile.organization:
            raise AuthenticationFailed("User organization context invalid")

        profile = user.profile
        organization = profile.organization

        return {
            "access_token": data["access"],
            "refresh_token": data["refresh"],  # NEW rotated refresh
            "expires_in": settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].seconds,
            "org_id": str(organization.external_id),
            "role": profile.role,
        }


# ==============================
# LOGOUT SERIALIZER
# ==============================
class AppLogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

    def validate(self, attrs):
        refresh_token = attrs.get("refresh_token")

        if not refresh_token:
            raise serializers.ValidationError("Refresh token is required")

        try:
            self.token = RefreshToken(refresh_token)
        except TokenError:
            raise AuthenticationFailed("Invalid or expired refresh token")

        return attrs

    def save(self, **kwargs):
        try:
            self.token.blacklist()
        except Exception:
            raise AuthenticationFailed("Token could not be blacklisted")
