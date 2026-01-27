from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.clinical_ops.models import AssessmentOrder
from apps.clinical_ops.services.access_code import issue_report_access_code
from apps.clinical_ops.audit.logger import log_event
from rest_framework.throttling import AnonRateThrottle

class PublicRequestReportCode(APIView):
    authentication_classes = []
    permission_classes = []
    throttle_classes = [AnonRateThrottle]

    def post(self, request, token):
        order = get_object_or_404(AssessmentOrder, public_token=token)

        # only if patient copy allowed
        if order.delivery_mode != AssessmentOrder.DELIVERY_ALLOW_PATIENT_DOWNLOAD:
            return Response({"error":"patient_download_not_allowed"}, status=403)

        code = issue_report_access_code(order, minutes_valid=15)

        # NOTE: We return code for now (dev).
        # Later: send via SMS/email gateway. For approvals, keep audit event.
        log_event(
            org_id=order.org_id,
            event_type="REPORT_ACCESS_CODE_ISSUED",
            entity_type="AssessmentOrder",
            entity_id=order.id,
            actor_role="Patient",
            details={"expires_minutes": 15}
        )

        return Response({"ok": True, "access_code": code, "expires_in_minutes": 15}, status=status.HTTP_200_OK)
