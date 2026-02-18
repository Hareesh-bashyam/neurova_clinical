import secrets
import re
from datetime import timedelta

from django.utils import timezone
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from common.encryption_decorators import decrypt_request, encrypt_response

from apps.clinical_ops.models import Patient, AssessmentOrder
from apps.clinical_ops.api.v1.serializers import (
    OrderCreateSerializer,
    QueueListSerializer,
)

from apps.clinical_ops.services.retention_policy import compute_retention_date
from backend.clinical.policies.services import get_or_create_policy
from apps.clinical_ops.models_public_token import PublicAccessToken



VALID_GENDERS = {"MALE", "FEMALE", "OTHER"}


def _make_token():
    return secrets.token_urlsafe(32)[:64]


# ============================================================
# CREATE PATIENT
# ============================================================
class CreatePatient(APIView):
    permission_classes = [IsAuthenticated]

    @decrypt_request
    @encrypt_response
    def post(self, request):
        data = request.decrypted_data

        # Logged-in user's organization (TRUSTED)
        user_org = request.user.profile.organization

        # Validate org_id from request (UUID / external_id)
        req_org_id = data.get("org_id")
        if not req_org_id:
            return Response(
                {
                    "success": False,
                    "message": "organization id is required",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if str(user_org.external_id) != str(req_org_id):
            return Response(
                {
                    "success": False,
                    "message": "Unauthorized organization access",
                    "data": None,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # ---- Required fields ----
        required_fields = ["full_name", "age", "sex", "phone", "email"]
        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                return Response(
                    {
                        "success": False,
                        "message": f"Missing field: {field}",
                        "data": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # ---- full_name ----
        full_name = data["full_name"].strip()
        if len(full_name) < 3:
            return Response(
                {
                    "success": False,
                    "message": "Full Name must be at least 3 characters",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---- age ----
        try:
            age = int(data["age"])
            if age < 0 or age > 120:
                raise ValueError
        except Exception:
            return Response(
                {
                    "success": False,
                    "message": "Age must be between 0 and 120",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---- sex ----
        sex = data["sex"].strip().upper()
        if sex not in VALID_GENDERS:
            return Response(
                {
                    "success": False,
                    "message": "Invalid Gender. Allowed: MALE, FEMALE, OTHER",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---- phone ----
        phone = data["phone"].strip()
        if not phone.isdigit() or not (8 <= len(phone) <= 15):
            return Response(
                {
                    "success": False,
                    "message": "Invalid Phone Number",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---- email ----
        email = data["email"].strip().lower()
        email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        if not re.match(email_regex, email):
            return Response(
                {
                    "success": False,
                    "message": "Invalid Email Address",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        mrn = data.get("mrn") or None

        patient = Patient.objects.create(
            org=user_org,  # ENFORCED
            mrn=mrn,
            full_name=full_name,
            age=age,
            sex=sex,
            phone=phone,
            email=email,
        )

        return Response(
            {
                "success": True,
                "message": "Patient created successfully",
                "data": {"patient_id": patient.id},
            },
            status=status.HTTP_201_CREATED,
        )


# ============================================================
# CREATE ORDER
# ============================================================
class CreateOrder(APIView):
    permission_classes = [IsAuthenticated]

    @decrypt_request
    @encrypt_response
    def post(self, request):
        serializer = OrderCreateSerializer(data=request.decrypted_data)
        if not serializer.is_valid():
            field, errors = next(iter(serializer.errors.items()))
            return Response(
                {
                    "success": False,
                    "message": f"{field}: {errors[0]}",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_org = request.user.profile.organization

        # Validate org_id (UUID)
        req_org_id = request.decrypted_data.get("org_id")
        if not req_org_id:
            return Response(
                {
                    "success": False,
                    "message": "Organization id is required",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if str(user_org.external_id) != str(req_org_id):
            return Response(
                {
                    "success": False,
                    "message": "Unauthorized organization access",
                    "data": None,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        patient = get_object_or_404(
            Patient,
            id=serializer.validated_data["patient_id"],
            org=user_org,  # ENFORCED
        )

        # token = _make_token()
        # policy = get_or_create_policy(user_org.id)
        # expires = timezone.now() + timedelta(
        #     hours=policy.token_validity_hours if policy else 48
        # )

        # ===============================
        # SECURE PUBLIC TOKEN CREATION
        # ===============================

        # Create order WITHOUT storing raw token
        order = AssessmentOrder.objects.create(
            org=user_org,
            patient=patient,
            battery_code=serializer.validated_data["battery_code"],
            battery_version=serializer.validated_data.get("battery_version", "1.0"),
            encounter_type=serializer.validated_data.get("encounter_type", "OPD"),
            referring_unit=serializer.validated_data.get("referring_unit"),
            administration_mode=serializer.validated_data.get(
                "administration_mode", AssessmentOrder.MODE_KIOSK
            ),
            verified_by_staff=serializer.validated_data.get("verified_by_staff", True),
            status=AssessmentOrder.STATUS_IN_PROGRESS,
            created_by_user_id=str(request.user.id),

            # ----------------------------------------
            # LEGACY METHOD (DO NOT USE ANYMORE)
            # public_token=token,
            # public_link_expires_at=expires,
            # ----------------------------------------
        )

        # Generate secure rotating token
        raw_token = PublicAccessToken.generate_raw_token()

        expires_at = timezone.now() + timedelta(minutes=5)

        PublicAccessToken.objects.create(
            order=order,
            token_hash=PublicAccessToken.hash_token(raw_token),
            expires_at=expires_at
        )

        order.data_retention_until = compute_retention_date(order.created_at)
        order.save(update_fields=["data_retention_until"])

        return Response(
            {
                "success": True,
                "message": "Patient Registered successfully",
                "data": {
                    "order_id": order.id,
                    "public_token": raw_token,
                    "public_link_expires_at": expires_at.isoformat(),
                },
            },
            status=status.HTTP_201_CREATED,
        )


# ============================================================
# CLINIC QUEUE
# ============================================================
class ClinicQueue(APIView):
    permission_classes = [IsAuthenticated]

    @encrypt_response
    def get(self, request):
        user_org = request.user.profile.organization

        qs = (
            AssessmentOrder.objects
            .filter(org=user_org)  # ALREADY ISOLATED
            .order_by("-created_at")[:200]
        )

        data = QueueListSerializer(qs, many=True).data

        return Response(
            {
                "success": True,
                "message": "Queue fetched successfully",
                "data": {"results": data},
            },
            status=status.HTTP_200_OK,
        )
