from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.files.base import ContentFile

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.clinical_ops.models import Org, AssessmentOrder
from apps.clinical_ops.models_report import AssessmentReport
from apps.clinical_ops.models_assessment import AssessmentResult

from apps.clinical_ops.services.report_context import build_report_context
from apps.clinical_ops.services.pdf_report_v2 import generate_report_pdf_bytes_v2
from apps.clinical_ops.services.signoff_engine import system_sign_report


class GenerateReportPDF(APIView):
    def post(self, request):
        org_id = request.data.get("org_id")
        order_id = request.data.get("order_id")

        if not org_id or not order_id:
            return Response(
                {"error": "org_id and order_id required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        org = get_object_or_404(Org, id=org_id, is_active=True)
        order = get_object_or_404(AssessmentOrder, id=order_id, org=org)

        # Allowed states only
        if order.status not in ["AWAITING_REVIEW", "DELIVERED", "COMPLETED"]:
            return Response(
                {"error": f"order status not allowed: {order.status}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create or fetch report row
        report, _ = AssessmentReport.objects.get_or_create(
            org_id=org.id,
            order=order,
            defaults={
                "generated_by_user_id": (
                    str(request.user.id)
                    if request.user and request.user.is_authenticated
                    else None
                ),
                "generated_at": timezone.now(),
            }
        )

        # =========================================================
        # 🔒 CRITICAL FIX — NORMALIZE RESULT JSON BEFORE SIGN-OFF
        # =========================================================
        result = AssessmentResult.objects.get(order=order)
        summary = result.result_json.setdefault("summary", {})
        summary.setdefault("has_red_flags", [])
        result.save(update_fields=["result_json"])
        # =========================================================

        # Build context AFTER normalization
        ctx = build_report_context(order)

        # Generate PDF
        pdf_bytes = generate_report_pdf_bytes_v2(ctx)

        filename = f"NEUROVAX_REPORT_ORDER_{order.id}.pdf"
        report.pdf_file.save(filename, ContentFile(pdf_bytes), save=True)

        # Auto system sign-off (mandatory)
        system_sign_report(
            report,
            actor_user=request.user if request.user.is_authenticated else None
        )

        # Update generation metadata
        report.generated_at = timezone.now()
        report.generated_by_user_id = (
            str(request.user.id)
            if request.user and request.user.is_authenticated
            else report.generated_by_user_id
        )
        report.save(update_fields=["generated_at", "generated_by_user_id", "pdf_file"])

        return Response(
            {
                "ok": True,
                "report_id": report.id,
                "pdf_url": report.pdf_file.url if report.pdf_file else None,
            },
            status=status.HTTP_200_OK
        )
