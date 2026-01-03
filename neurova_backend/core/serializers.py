from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Organization, UserProfile

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = "__all__"

class UserCreateSerializer(serializers.ModelSerializer):
    role = serializers.CharField(write_only=True)
    organization_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "password", "email", "role", "organization_id"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        role = validated_data.pop("role")
        org_id = validated_data.pop("organization_id")

        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(
            user=user,
            organization_id=org_id,
            role=role,
        )
        return user
