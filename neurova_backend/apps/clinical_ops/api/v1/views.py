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
from datetime import timedelta
from backend.clinical.policies.services import get_or_create_policy

def _make_token():
    return secrets.token_urlsafe(32)[:64]

VALID_GENDERS = {"MALE", "FEMALE", "OTHER"}

class CreatePatient(APIView):

    def post(self, request):
        data = request.data

        # ---- STEP 1: Required fields ----
        required = [
            "org_id",
            "full_name",
            "age",
            "sex",
        ]

        for field in required:
            if field not in data:
                return Response(
                    {
                        "success": False,
                        "message": f"Missing field: {field}",
                        "data": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # ---- STEP 2: Organization validation ----
        org = Org.objects.filter(
            id=data["org_id"],
            is_active=True
        ).first()

        if not org:
            return Response(
                {
                    "success": False,
                    "message": "Invalid or inactive organization",
                    "data": None,
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # ---- STEP 3: full_name validation ----
        full_name = str(data.get("full_name")).strip()
        if len(full_name) < 3:
            return Response(
                {
                    "success": False,
                    "message": "full_name must be at least 3 characters",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---- STEP 4: age validation ----
        try:
            age = int(data.get("age"))
        except (TypeError, ValueError):
            return Response(
                {
                    "success": False,
                    "message": "age must be an integer",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if age < 0 or age > 120:
            return Response(
                {
                    "success": False,
                    "message": "age must be between 0 and 120",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---- sex validation ----
        sex = data.get("sex")

        if not sex:
            return Response(
                {
                    "success": False,
                    "message": "Missing field: sex",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        sex = str(sex).strip().upper()

        if sex not in VALID_GENDERS:
            return Response(
                {
                    "success": False,
                    "message": "Invalid sex. Allowed: MALE, FEMALE, OTHER",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---- STEP 6: optional fields ----
        mrn = data.get("mrn") or None
        phone = data.get("phone") or None
        email = data.get("email") or None

        # ---- STEP 7: create patient ----
        patient = Patient.objects.create(
            org=org,
            mrn=mrn,
            full_name=full_name,
            age=age,
            sex=sex,
            phone=phone,
            email=email,
        )

        # ---- STEP 8: success response ----
        return Response(
            {
                "success": True,
                "message": "Patient created successfully",
                "data": {
                    "patient_id": patient.id,
                },
            },
            status=status.HTTP_201_CREATED,
        )

    

class CreateOrder(APIView):
    def post(self, request):
        s = OrderCreateSerializer(data=request.data)

        # ---- VALIDATION HANDLING (FIX) ----
        if not s.is_valid():
            first_field, errors = next(iter(s.errors.items()))
            first_error = errors[0]

            return Response(
                {
                    "success": False,
                    "message": f"{first_field}: {first_error}",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---- BUSINESS LOGIC ----
        org = get_object_or_404(Org, id=s.validated_data["org_id"], is_active=True)
        patient = get_object_or_404(
            Patient, id=s.validated_data["patient_id"], org=org
        )

        token = _make_token()
        policy = get_or_create_policy(org.id)
        hours = (
            policy.token_validity_hours
            if policy and policy.token_validity_hours
            else 48
        )
        expires = timezone.now() + timedelta(hours=hours)

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
            # created_by_user_id=(
            #     str(request.user.id)
            #     if getattr(request, "user", None) and request.user.is_authenticated
            #     else None
            # ),
            public_token=token,
            public_link_expires_at=expires,
        )

        order.data_retention_until = compute_retention_date(order.created_at)
        order.save(update_fields=["data_retention_until"])

        return Response(
            {
                "success": True,
                "message": "Order created successfully",
                "data": {
                    "order_id": order.id,
                    "public_token": order.public_token,
                    "public_link_expires_at": order.public_link_expires_at.isoformat(),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class ClinicQueue(APIView):
    def get(self, request):
        org_id = request.query_params.get("org_id")

        # ---- STEP 1: required param ----
        if not org_id:
            return Response(
                {
                    "success": False,
                    "message": "org_id is required",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---- STEP 2: org validation (NO get_object_or_404) ----
        org = Org.objects.filter(
            id=org_id,
            is_active=True
        ).first()

        if not org:
            return Response(
                {
                    "success": False,
                    "message": "Invalid or inactive organization",
                    "data": None,
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # ---- STEP 3: fetch queue ----
        qs = (
            AssessmentOrder.objects
            .filter(org=org)
            .order_by("-created_at")[:200]
        )

        data = QueueListSerializer(qs, many=True).data

        # ---- STEP 4: success response ----
        return Response(
            {
                "success": True,
                "message": "Queue fetched successfully",
                "data": {
                    "results": data,
                },
            },
            status=status.HTTP_200_OK,
        )
