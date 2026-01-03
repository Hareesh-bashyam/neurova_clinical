from rest_framework import serializers
from .models import Patient


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = [
            "id",
            "external_id",
            "name",
            "dob",
            "sex",
            "phone",
            "email",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
