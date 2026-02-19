import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from django.shortcuts import get_object_or_404

from common.encryption_decorators import decrypt_request, encrypt_response

from apps.clinical_ops.models import AssessmentOrder
from apps.clinical_ops.audit.logger import log_event


logger = logging.getLogger(__name__)


class PatientAcceptRejectOrder(APIView):
    """
    API endpoint for staff to mark an assessment order as accepted or rejected on behalf of patient.
    
    POST /api/v1/clinical/staff/order/<order_id>/accept-reject
    
    Request Body (encrypted):
    {
        "action": "ACCEPT" or "REJECT" or "REMARK",
        "data": "Optional remark field"
    }
    
    Response (encrypted):
    {
        "success": true,
        "message": "Order accepted successfully",
        "data": {
            "order_id": 123,
            "status": "ACCEPTED",
            "patient_acceptance_timestamp": "2026-02-17T20:30:00Z"
        }
    }
    """
    permission_classes = [IsAuthenticated]

    @decrypt_request
    @encrypt_response
    def post(self, request, order_id):
        try:
            # Org Isolation
            user_org = request.user.profile.organization
            
            # Fetch Order
            order = get_object_or_404(
                AssessmentOrder,
                pk=order_id,
                org=user_org
            )

            # Get action from request
            action = request.decrypted_data.get("action", "").upper()
            notes = request.decrypted_data.get("notes", "") or request.decrypted_data.get("reason", "")
            data = request.decrypted_data.get("data", "")

            # Validate action
            if action not in ["ACCEPT", "REJECT","REMARK"]:
                return Response({
                    "success": False,
                    "message": "Invalid action. Must be 'ACCEPT' or 'REJECT'.",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)


            # Update order status
            # Update order status
            if action == "ACCEPT":
                order.status = AssessmentOrder.STATUS_ACCEPTED
                message = "Accepted"
                event_type = "ORDER_ACCEPTED_BY_DOCTOR"
            elif action == "REMARK":
                order.patient_acceptance_remark = data if data else None
                message = "Remark added"
                event_type = "ORDER_REMARK_BY_DOCTOR"
            else:  # REJECT
                order.status = AssessmentOrder.STATUS_REJECTED
                message = "Rejected"
                event_type = "ORDER_REJECTED_BY_DOCTOR"
                # order.patient_acceptance_notes = notes if notes else None
                order.patient_acceptance_notes = data if data else None

            order.patient_acceptance_timestamp = timezone.now()

            order.save(update_fields=[
                "status",
                "patient_acceptance_timestamp",
                "patient_acceptance_notes",
                "patient_acceptance_remark"
            ])

            # Log audit event
            log_event(
                org=order.org,
                event_type=event_type,
                entity_type="AssessmentOrder",
                entity_id=order.id,
                actor_user_id=str(request.user.id),
                actor_role=request.user.profile.role,
                details={
                    "action": action,
                    "notes": notes,
                    "remark": data,
                    "patient_name": order.patient.full_name,
                    "battery_code": order.battery_code
                },
                request=request,
                severity="INFO"
            )

            return Response({
                "success": True,
                "message": message,
                "data": {
                    "order_id": order.id,
                    "status": order.status,
                    "patient_acceptance_timestamp": order.patient_acceptance_timestamp.isoformat() if order.patient_acceptance_timestamp else None
                }
            }, status=status.HTTP_200_OK)

        except PermissionDenied as e:
            return Response({
                "success": False,
                "message": str(e),
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        except ValidationError as e:
            return Response({
                "success": False,
                "message": str(e),
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # Log the error for debugging
            logger.error(f"Error in PatientAcceptRejectOrder: {str(e)}", exc_info=True)

            return Response({
                "success": False,
                "message": "Unable to process your request at this time.",
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
