from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.files.base import ContentFile

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.clinical_ops.models import AssessmentOrder
from core.models import Organization
from apps.clinical_ops.models_report import AssessmentReport
from apps.clinical_ops.models_assessment import AssessmentResult

from apps.clinical_ops.services.report_context import build_report_context
from apps.clinical_ops.services.pdf_report_v2 import generate_report_pdf_bytes_v2
from apps.clinical_ops.services.signoff_engine import system_sign_report
import hashlib


class GenerateReportPDF(APIView):
    def post(self, request):
        org_id = request.data.get("org_id")
        order_id = request.data.get("order_id")

        if not org_id or not order_id:
            return Response(
                {
                    "success": False,
                    "message": "org_id and order_id required",
                    "data": None
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # 🔐 Resolve org via external_id
        org = get_object_or_404(Organization, external_id=org_id)

        # 🔒 Enforce user belongs to org
        if request.user.profile.organization_id != org.id:
            return Response(
                {
                    "success": False,
                    "message": "Unauthorized organization access",
                    "data": None
                },
                status=status.HTTP_403_FORBIDDEN
            )

        order = get_object_or_404(
            AssessmentOrder,
            id=order_id,
            org=org
        )

        if order.status not in ["AWAITING_REVIEW", "DELIVERED", "COMPLETED"]:
            return Response(
                {
                    "success": False,
                    "message": f"order status not allowed: {order.status}",
                    "data": None
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        report, _ = AssessmentReport.objects.get_or_create(
            org=org,
            order=order,
            defaults={
                "generated_by_user_id": str(request.user.id),
                "generated_at": timezone.now(),
            }
        )

        result = AssessmentResult.objects.filter(order=order).first()
        if not result:
            return Response(
                {
                    "success": False,
                    "message": "Assessment result not available yet",
                    "data": None
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        summary = result.result_json.setdefault("summary", {})
        summary.setdefault("has_red_flags", [])
        result.save(update_fields=["result_json"])

        ctx = build_report_context(order)
        pdf_bytes = generate_report_pdf_bytes_v2(ctx)

        filename = f"NEUROVAX_REPORT_ORDER_{order.id}.pdf"
        report.pdf_file.save(filename, ContentFile(pdf_bytes), save=True)

        report.pdf_file.open("rb")
        report.pdf_sha256 = hashlib.sha256(report.pdf_file.read()).hexdigest()
        report.pdf_file.close()

        report.generated_at = timezone.now()
        report.generated_by_user_id = str(request.user.id)
        report.save()

        system_sign_report(report, actor_user=request.user)

        return Response(
            {
                "success": True,
                "message": "Report generated successfully",
                "data": {
                    "report_id": report.id,
                    "pdf_url": report.pdf_file.url
                }
            },
            status=status.HTTP_200_OK
        )
