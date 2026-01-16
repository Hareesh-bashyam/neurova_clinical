from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.clinical_ops.models import Org, AssessmentOrder
from apps.clinical_ops.models_report import AssessmentReport
from apps.clinical_ops.services.access_code import verify_report_access_code


class StaffDownloadReport(APIView):
    def get(self, request):
        org_id = request.query_params.get("org_id")
        order_id = request.query_params.get("order_id")
        if not org_id or not order_id:
            return Response({"error": "org_id and order_id required"}, status=400)

        org = get_object_or_404(Org, id=org_id, is_active=True)
        order = get_object_or_404(AssessmentOrder, id=order_id, org=org)
        report = get_object_or_404(AssessmentReport, order=order, org=org)

        if not report.pdf_file:
            return Response({"error": "pdf_not_generated"}, status=404)

        return FileResponse(
            report.pdf_file.open("rb"),
            content_type="application/pdf"
        )


class PublicDownloadReport(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, token):
        order = get_object_or_404(AssessmentOrder, public_token=token)

        # expiry check
        if order.public_link_expires_at and timezone.now() > order.public_link_expires_at:
            return Response({"error": "link_expired"}, status=403)

        # Delivery rule: patient download only if explicitly allowed
        if order.delivery_mode != AssessmentOrder.DELIVERY_ALLOW_PATIENT_DOWNLOAD:
            return Response({"error": "patient_download_not_allowed"}, status=403)

        # 🔐 OTP / access-code required
        code = request.query_params.get("code")
        if not code or not verify_report_access_code(order, code):
            return Response(
                {"error": "access_code_required_or_invalid"},
                status=403
            )

        report = get_object_or_404(AssessmentReport, order=order)

        if not report.pdf_file:
            return Response({"error": "pdf_not_generated"}, status=404)

        return FileResponse(
            report.pdf_file.open("rb"),
            content_type="application/pdf"
        )
