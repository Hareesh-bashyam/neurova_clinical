from django.utils import timezone
from rest_framework import serializers
from apps.clinical_ops.models import AssessmentOrder


# ============================================================
# ORDER CREATE (STAFF)
# ============================================================
class OrderCreateSerializer(serializers.Serializer):
    patient_id = serializers.IntegerField()
    battery_code = serializers.CharField()
    battery_version = serializers.CharField(required=False, default="1.0")
    encounter_type = serializers.CharField(required=False, default="OPD")
    referring_unit = serializers.CharField(required=False, allow_blank=True)
    administration_mode = serializers.ChoiceField(
        choices=[
            AssessmentOrder.MODE_KIOSK,
            AssessmentOrder.MODE_QR_PHONE,
            AssessmentOrder.MODE_ASSISTED,
        ],
        required=False,
        default=AssessmentOrder.MODE_KIOSK,
    )
    verified_by_staff = serializers.BooleanField(required=False, default=True)


# ============================================================
# CLINIC QUEUE LIST
# ============================================================
class QueueListSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    patient_age = serializers.IntegerField(source="patient.age", read_only=True)
    patient_sex = serializers.CharField(source="patient.sex", read_only=True)

    public_token = serializers.SerializerMethodField()

    class Meta:
        model = AssessmentOrder
        fields = [
            "id",
            "status",
            "battery_code",
            "battery_version",
            "encounter_type",
            "administration_mode",
            "created_at",
            "started_at",
            "completed_at",
            "patient_name",
            "patient_age",
            "patient_sex",
            "public_token",
        ]

    def get_public_token(self, obj):
        # Fetch latest token that is NOT expired
        token = (
            obj.secure_tokens
            .filter(is_used=False, is_locked=False, expires_at__gt=timezone.now())
            .order_by("-created_at")
            .first()
        )
        if token:
           # We cannot return raw token because we only store hash!
           # We can only return a placeholder or boolean indicating a valid link exists.
           # BUT if the user wants the link to work, they MUST generate a new one on demand.
           # However, for now, let's just return True/False or the count.
           return "HIDDEN_FOR_SECURITY" 
           # NOTE TO USER: We only store HASHES. We cannot retrieve the raw token to show in the list.
           # The frontend must call a specific endpoint to "Generate Link" which returns a new raw token.
