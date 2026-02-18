import logging
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import AnonRateThrottle

from apps.clinical_ops.models import AssessmentOrder
from apps.clinical_ops.services.access_code import issue_report_access_code
from apps.clinical_ops.audit.logger import log_event


logger = logging.getLogger(__name__)


class PublicRequestReportCode(APIView):
    authentication_classes = []
    permission_classes = []
    throttle_classes = [AnonRateThrottle]

    def post(self, request, token):
        try:
            order = get_object_or_404(
                AssessmentOrder,
                public_token=token,
                deletion_status="ACTIVE",
            )
    
            # Public link expiry check
            if order.public_link_expires_at and timezone.now() > order.public_link_expires_at:
                return Response(
                    {
                        "success": False,
                        "message": "Link expired",
                        "data": None
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
    
            # Patient download policy
            if order.delivery_mode != AssessmentOrder.DELIVERY_ALLOW_PATIENT_DOWNLOAD:
                return Response(
                    {
                        "success": False,
                        "message": "Patient download not allowed",
                        "data": None
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
    
            # Issue short-lived access code
            code = issue_report_access_code(order, minutes_valid=15)
    
            # Audit event
            log_event(
                org_id=order.org.id,
                event_type="REPORT_ACCESS_CODE_ISSUED",
                entity_type="AssessmentOrder",
                entity_id=order.id,
                actor_role="Patient",
                details={
                    "expires_minutes": 15,
                },
            )
    
            return Response(
                {
                    "success": True,
                    "message": "Report access code issued successfully",
                    "data": {
                        "access_code": code,          # dev-only (remove in prod)
                        "expires_in_minutes": 15,
                        "public_token": token
                    },
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error requesting report code: {str(e)}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "message": "Unable to request access code at this time.",
                    "data": None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
