import hashlib

from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from apps.clinical_ops.models import Org, AssessmentOrder
from apps.clinical_ops.models_report import AssessmentReport
from apps.clinical_ops.services.access_code import verify_report_access_code


# =================================================
# STAFF DOWNLOAD (INTERNAL)
# =================================================
class StaffDownloadReport(APIView):
    def get(self, request):
        org_id = request.query_params.get("org_id")
        order_id = request.query_params.get("order_id")

        if not org_id or not order_id:
            return Response(
                {
                    "success": False,
                    "message": "org_id and order_id required",
                    "data":None
                },
                status=400,
            )

        org = get_object_or_404(Org, id=org_id, is_active=True)
        order = get_object_or_404(AssessmentOrder, id=order_id, org=org)
        report = get_object_or_404(AssessmentReport, order=order, org=org)

        if not report.pdf_file:
            return Response({
                "success": False,
                "message": "PDF not generated",
                "data":None
            }, status=404)

        # 🔐 ANTI-TAMPER CHECK
        report.pdf_file.open("rb")
        pdf_bytes = report.pdf_file.read()
        report.pdf_file.close()

        current_hash = hashlib.sha256(pdf_bytes).hexdigest()

        if report.pdf_sha256 and current_hash != report.pdf_sha256:
            return Response(
                {
                    "success": False,
                    "message": "PDF integrity check failed",
                    "data":None
                },
                status=409,
            )

        return FileResponse(
            report.pdf_file.open("rb"),
            content_type="application/pdf",
        )


# =================================================
# PUBLIC DOWNLOAD (PATIENT)
# =================================================
class PublicDownloadReport(APIView):
    authentication_classes = []
    permission_classes = []
    throttle_classes = [AnonRateThrottle]

    def get(self, request, token):
        order = get_object_or_404(AssessmentOrder, public_token=token)

        # ⏳ Expiry check
        if order.public_link_expires_at and timezone.now() > order.public_link_expires_at:
            return Response({
                "success": False,
                "message": "Link expired",
                "data":None
            }, status=403)

        # 🚫 Patient download policy
        if order.delivery_mode != AssessmentOrder.DELIVERY_ALLOW_PATIENT_DOWNLOAD:
            return Response(
                {
                    "success": False,
                    "message": "Patient download not allowed",
                    "data":None
                },
                status=403,
            )

        # 🔐 Access code required
        code = request.query_params.get("code")
        if not code or not verify_report_access_code(order, code):
            return Response(
                {"error": "access_code_required_or_invalid"},
                status=403,
            )

        report = get_object_or_404(AssessmentReport, order=order)

        if not report.pdf_file:
            return Response({
                "success": False,
                "message": "PDF not generated",
                "data":None
            }, status=404)

        # 🔐 ANTI-TAMPER CHECK
        report.pdf_file.open("rb")
        pdf_bytes = report.pdf_file.read()
        report.pdf_file.close()

        current_hash = hashlib.sha256(pdf_bytes).hexdigest()

        if report.pdf_sha256 and current_hash != report.pdf_sha256:
            return Response(
                {
                    "success": False,
                    "message": "PDF integrity check failed",
                    "data":None
                },
                status=409,
            )

        return FileResponse(
            report.pdf_file.open("rb"),
            content_type="application/pdf",
        )
