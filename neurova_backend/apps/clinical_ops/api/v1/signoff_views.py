from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.clinical_ops.models import AssessmentOrder
from apps.clinical_ops.models_report import AssessmentReport
from apps.clinical_ops.audit.logger import log_event


class OverrideReportSignoff(APIView):
    """
    Clinician overrides system signoff.

    Payload:
    {
      "order_id": 123,
      "signoff_status": "SIGNED" | "REJECTED",
      "signed_by_name": "Dr X",
      "signed_by_role": "Psychiatrist",
      "reason": "manual review completed"
    }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        org = request.user.profile.organization  # TRUSTED ORG

        order_id = request.data.get("order_id")
        signoff_status = request.data.get("signoff_status")
        signed_by_name = request.data.get("signed_by_name")
        signed_by_role = request.data.get("signed_by_role")
        reason = request.data.get("reason")

        if not all([order_id, signoff_status, signed_by_name, signed_by_role, reason]):
            return Response(
                {
                    "success": False,
                    "message": "order id, signoff status, signed by name, signed by role, reason required",
                    "data": None
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if signoff_status not in {"SIGNED", "REJECTED"}:
            return Response(
                {
                    "success": False,
                    "message": "signoff status must be SIGNED or REJECTED",
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

        # Lifecycle guard
        if order.status not in {
            AssessmentOrder.STATUS_COMPLETED,
            AssessmentOrder.STATUS_AWAITING_REVIEW,
            AssessmentOrder.STATUS_DELIVERED,
        }:
            return Response(
                {
                    "success": False,
                    "message": f"Cannot override signoff for order in status {order.status}",
                    "data": None
                },
                status=status.HTTP_409_CONFLICT,
            )

        report = get_object_or_404(
            AssessmentReport,
            order=order,
            org=org,
        )

        report.signoff_status = signoff_status
        report.signoff_method = "CLINICIAN"
        report.signed_by_name = signed_by_name
        report.signed_by_role = signed_by_role
        report.signed_at = timezone.now()
        report.signoff_reason = reason

        report.save(
            update_fields=[
                "signoff_status",
                "signoff_method",
                "signed_by_name",
                "signed_by_role",
                "signed_at",
                "signoff_reason",
            ]
        )

        # AUDIT LOG (KEEP THIS — VERY GOOD)
        log_event(
            org_id=org.id,
            event_type="REPORT_SIGNOFF_OVERRIDE",
            entity_type="AssessmentReport",
            entity_id=report.id,
            actor_user_id=str(request.user.id),
            actor_name=signed_by_name,
            actor_role=signed_by_role,
            details={
                "status": signoff_status,
                "reason": reason,
                "method": "CLINICIAN",
            },
        )

        return Response(
            {
                "success": True,
                "message": "Report signoff overridden successfully",
                "data": {
                    "order_id": order.id,
                    "signoff_status": report.signoff_status,
                    "method": report.signoff_method,
                },
            },
            status=status.HTTP_200_OK,
        )
