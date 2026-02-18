import logging
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.files.base import ContentFile
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from common.encryption_decorators import decrypt_request, encrypt_response

from apps.clinical_ops.models import AssessmentOrder
from core.models import Organization
from apps.clinical_ops.models_report import AssessmentReport
from apps.clinical_ops.models_assessment import AssessmentResult
from apps.clinical_ops.services.report_context import build_report_context
from apps.clinical_ops.services.pdf_report_v2 import generate_report_pdf_bytes_v2
from apps.clinical_ops.services.signoff_engine import system_sign_report
from apps.clinical_ops.audit.logger import log_event

import hashlib


logger = logging.getLogger(__name__)


class GenerateReportPDF(APIView):
    permission_classes = [IsAuthenticated]

    @decrypt_request
    @encrypt_response
    @transaction.atomic
    def post(self, request):

        try:
            org_id = request.decrypted_data.get("org_id")
            order_id = request.decrypted_data.get("order_id")

            if not org_id or not order_id:
                return Response(
                    {
                        "success": False,
                        "message": "Organization and order id required",
                        "data": None
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            org = get_object_or_404(Organization, external_id=org_id)

            if request.user.profile.organization_id != org.id:
                return Response(
                    {
                        "success": False,
                        "message": "Unauthorized organization access",
                        "data": None
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

            order = (
                AssessmentOrder.objects
                .select_for_update()
                .get(id=order_id, org=org)
            )

            if order.status not in [
                AssessmentOrder.STATUS_AWAITING_REVIEW,
                AssessmentOrder.STATUS_DELIVERED,
                AssessmentOrder.STATUS_COMPLETED
            ]:
                return Response(
                    {
                        "success": False,
                        "message": f"Order status not allowed: {order.status}",
                        "data": None
                    },
                    status=status.HTTP_400_BAD_REQUEST
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

            report, _ = AssessmentReport.objects.get_or_create(
                org=org,
                order=order,
                defaults={
                    "generated_by_user_id": str(request.user.id),
                    "generated_at": timezone.now(),
                }
            )

            ctx = build_report_context(order)
            pdf_bytes = generate_report_pdf_bytes_v2(ctx)

            filename = f"NEUROVAX_REPORT_ORDER_{order.id}.pdf"
            report.pdf_file.save(filename, ContentFile(pdf_bytes), save=True)

            report.pdf_sha256 = hashlib.sha256(pdf_bytes).hexdigest()
            report.generated_at = timezone.now()
            report.generated_by_user_id = str(request.user.id)
            report.save()

            system_sign_report(report, actor_user=request.user)

            # 🔐 Audit log
            log_event(
                org=org,
                event_type="REPORT_GENERATED",
                entity_type="AssessmentOrder",
                entity_id=order.id,
                actor_user_id=str(request.user.id),
                actor_name=request.user.username,
                actor_role=request.user.profile.role,
                request=request,
                severity="SECURITY"
            )

            return Response(
                {
                    "success": True,
                    "message": "Report Generated Successfully",
                    "data": {
                        "report_id": report.id,
                        "pdf_url": report.pdf_file.url
                    }
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error generating report: {str(e)}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "message": "Unable to generate report at this time.",
                    "data": None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
