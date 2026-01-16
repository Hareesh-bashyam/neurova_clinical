from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.clinical_ops.models import Org, Patient, AssessmentOrder
from apps.clinical_ops.api.v1.serializers import (
    PatientCreateSerializer,
    OrderCreateSerializer,
    QueueListSerializer,
)
import secrets
from apps.clinical_ops.services.retention_policy import compute_retention_date

def _make_token():
    return secrets.token_urlsafe(32)[:64]

class CreatePatient(APIView):
    def post(self, request):
        s = PatientCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        org = get_object_or_404(Org, id=s.validated_data["org_id"], is_active=True)

        patient = Patient.objects.create(
            org=org,
            mrn=s.validated_data.get("mrn") or None,
            full_name=s.validated_data["full_name"],
            age=s.validated_data["age"],
            sex=s.validated_data["sex"],
            phone=s.validated_data.get("phone") or None,
            email=s.validated_data.get("email") or None,
        )
        return Response({"patient_id": patient.id}, status=status.HTTP_201_CREATED)


class CreateOrder(APIView):
    def post(self, request):
        s = OrderCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        org = get_object_or_404(Org, id=s.validated_data["org_id"], is_active=True)
        patient = get_object_or_404(
            Patient, id=s.validated_data["patient_id"], org=org
        )

        token = _make_token()
        expires = timezone.now() + timezone.timedelta(days=2)

        order = AssessmentOrder.objects.create(
            org=org,
            patient=patient,
            battery_code=s.validated_data["battery_code"],
            battery_version=s.validated_data.get("battery_version") or "1.0",
            encounter_type=s.validated_data.get("encounter_type") or "OPD",
            referring_unit=s.validated_data.get("referring_unit") or None,
            administration_mode=(
                s.validated_data.get("administration_mode")
                or AssessmentOrder.MODE_KIOSK
            ),
            verified_by_staff=s.validated_data.get("verified_by_staff", True),
            status=AssessmentOrder.STATUS_CREATED,
            created_by_user_id=(
                str(request.user.id)
                if getattr(request, "user", None) and request.user.is_authenticated
                else None
            ),
            public_token=token,
            public_link_expires_at=expires,
        )

        # ✅ 15A.4 — Apply retention policy at creation time
        order.data_retention_until = compute_retention_date(order.created_at)
        order.save(update_fields=["data_retention_until"])

        return Response(
            {
                "order_id": order.id,
                "public_token": order.public_token,
                "public_link_expires_at": order.public_link_expires_at.isoformat(),
            },
            status=status.HTTP_201_CREATED,
        )


class ClinicQueue(APIView):
    def get(self, request):
        org_id = request.query_params.get("org_id")
        if not org_id:
            return Response({"error":"org_id is required"}, status=400)
        org = get_object_or_404(Org, id=org_id, is_active=True)

        qs = AssessmentOrder.objects.filter(org=org).order_by("-created_at")[:200]
        data = QueueListSerializer(qs, many=True).data
        return Response({"results": data})
