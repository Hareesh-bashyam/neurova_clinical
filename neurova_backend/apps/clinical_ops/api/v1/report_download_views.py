import hashlib

from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework import status

from apps.clinical_ops.models import AssessmentOrder
from apps.clinical_ops.models_report import AssessmentReport
from apps.clinical_ops.services.access_code import verify_report_access_code


# =================================================
# STAFF DOWNLOAD (INTERNAL)
# =================================================
class StaffDownloadReport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = request.user.profile.organization  # TRUSTED ORG
        order_id = request.query_params.get("order_id")

        if not order_id:
            return Response(
                {
                    "success": False,
                    "message": "Order id required",
                    "data": None
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        order = get_object_or_404(
            AssessmentOrder,
            id=order_id,
            org=org,
            deletion_status="ACTIVE",
        )

        report = get_object_or_404(
            AssessmentReport,
            order=order,
            org=org,
        )

        if not report.pdf_file:
            return Response(
                {
                    "success": False,
                    "message": "PDF not generated",
                    "data": None
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # ANTI-TAMPER CHECK
        with report.pdf_file.open("rb") as f:
            pdf_bytes = f.read()

        current_hash = hashlib.sha256(pdf_bytes).hexdigest()

        if report.pdf_sha256 and current_hash != report.pdf_sha256:
            return Response(
                {
                    "success": False,
                    "message": "PDF integrity check failed",
                    "data": None
                },
                status=status.HTTP_409_CONFLICT,
            )

        response = FileResponse(
            report.pdf_file.open("rb"),
            content_type="application/pdf",
        )

        response["Content-Disposition"] = (
            f'attachment; filename="assessment_report_{order.id}.pdf"'
        )

        return response


# =================================================
# PUBLIC DOWNLOAD (PATIENT)
# =================================================
class PublicDownloadReport(APIView):
    authentication_classes = []
    permission_classes = []
    throttle_classes = [AnonRateThrottle]

    def get(self, request, token):
        order = get_object_or_404(
            AssessmentOrder,
            public_token=token,
            deletion_status="ACTIVE",
        )

        # EXPIRY CHECK
        if order.public_link_expires_at and timezone.now() > order.public_link_expires_at:
            return Response(
                {
                    "success": False,
                    "message": "Link expired",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # DELIVERY POLICY CHECK
        if order.delivery_mode != AssessmentOrder.DELIVERY_ALLOW_PATIENT_DOWNLOAD:
            return Response(
                {
                    "success": False,
                    "message": "Patient download not allowed",
                    "data": None
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # ACCESS CODE CHECK
        code = request.query_params.get("code")
        if not code or not verify_report_access_code(order, code):
            return Response(
                {
                    "success": False,
                    "message": "Invalid or missing access code",
                    "data": None
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        report = get_object_or_404(
            AssessmentReport,
            order=order,
        )

        if not report.pdf_file:
            return Response(
                {
                    "success": False,
                    "message": "PDF not found",
                    "data": None
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        #  ANTI-TAMPER CHECK
        with report.pdf_file.open("rb") as f:
            pdf_bytes = f.read()

        current_hash = hashlib.sha256(pdf_bytes).hexdigest()

        if report.pdf_sha256 and current_hash != report.pdf_sha256:
            return Response(
                {
                    "success": False,
                    "message": "PDF integrity check failed",
                    "data": None
                },
                status=status.HTTP_409_CONFLICT,
            )

        response = FileResponse(
            report.pdf_file.open("rb"),
            content_type="application/pdf",
        )

        response["Content-Disposition"] = (
            f'attachment; filename="assessment_report_{order.id}.pdf"'
        )

        return response
