from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.clinical_ops.models import Org, AssessmentOrder
from apps.clinical_ops.models_report import AssessmentReport
from apps.clinical_ops.audit.logger import log_event

class OverrideReportSignoff(APIView):
    """
    Staff/Clinician can override system signoff:
    payload:
    {
      "org_id": 1,
      "order_id": 123,
      "signoff_status": "SIGNED" or "REJECTED",
      "signed_by_name": "Dr X",
      "signed_by_role": "Psychiatrist" or "Clinical Psychologist",
      "reason": "manual review completed"
    }
    """
    def post(self, request):
        org_id = request.data.get("org_id")
        order_id = request.data.get("order_id")

        signoff_status = request.data.get("signoff_status")
        signed_by_name = request.data.get("signed_by_name")
        signed_by_role = request.data.get("signed_by_role")
        reason = request.data.get("reason")

        if not all([org_id, order_id, signoff_status, signed_by_name, signed_by_role, reason]):
            return Response({"error":"org_id, order_id, signoff_status, signed_by_name, signed_by_role, reason required"}, status=400)

        if signoff_status not in ["SIGNED", "REJECTED"]:
            return Response({"error":"signoff_status must be SIGNED or REJECTED"}, status=400)

        org = get_object_or_404(Org, id=org_id, is_active=True)
        order = get_object_or_404(AssessmentOrder, id=order_id, org=org)
        report = get_object_or_404(AssessmentReport, order=order, org=org)

        report.signoff_status = signoff_status
        report.signoff_method = "CLINICIAN"
        report.signed_by_name = signed_by_name
        report.signed_by_role = signed_by_role
        report.signed_at = timezone.now()
        report.signoff_reason = reason
        report.save(update_fields=[
            "signoff_status","signoff_method","signed_by_name","signed_by_role","signed_at","signoff_reason"
        ])

        log_event(
            org_id=org.id,
            event_type="REPORT_SIGNOFF_OVERRIDE",
            entity_type="AssessmentReport",
            entity_id=report.id,
            actor_user_id=str(request.user.id) if request.user.is_authenticated else None,
            actor_name=signed_by_name,
            actor_role=signed_by_role,
            details={"status": signoff_status, "reason": reason, "method": "CLINICIAN"}
        )

        return Response({"ok": True, "signoff_status": report.signoff_status, "method": report.signoff_method}, status=200)
