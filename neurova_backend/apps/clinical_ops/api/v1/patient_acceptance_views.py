from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import AnonRateThrottle
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from django.shortcuts import get_object_or_404

from common.encryption_decorators import decrypt_request, encrypt_response

from apps.clinical_ops.models import AssessmentOrder
from apps.clinical_ops.services.public_token_validator import validate_and_rotate_url_token
from apps.clinical_ops.audit.logger import log_event


class PatientAcceptRejectOrder(APIView):
    """
    API endpoint for patients to accept or reject an assessment order.
    
    POST /api/v1/clinical/clinicaian/order/<order_id>/accept-reject
    
    Request Body (encrypted):
    {
        "action": "ACCEPT" or "REJECT",
        "notes": "Optional rejection reason or comments"
    }
    
    Response (encrypted):
    {
        "success": true,
        "message": "Order accepted successfully",
        "data": {
            "order_id": 123,
            "patient_acceptance_status": "ACCEPTED",
            "patient_acceptance_timestamp": "2026-02-17T20:30:00Z",
            "public_token": "new_rotated_token"
        }
    }
    """
    authentication_classes = []
    permission_classes = []
    throttle_classes = [AnonRateThrottle]

    @decrypt_request
    @encrypt_response
    def post(self, request, token):
        try:
            # Validate & Rotate Token
            order, new_token = validate_and_rotate_url_token(token, request)

            # Get action from request
            action = request.decrypted_data.get("action", "").upper()
            notes = request.decrypted_data.get("notes", "")

            # Validate action
            if action not in ["ACCEPT", "REJECT"]:
                return Response({
                    "success": False,
                    "message": "Invalid action. Must be 'ACCEPT' or 'REJECT'.",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if order can be accepted/rejected
            if order.patient_acceptance_status != AssessmentOrder.ACCEPTANCE_PENDING:
                return Response({
                    "success": False,
                    "message": f"Order has already been {order.patient_acceptance_status.lower()}.",
                    "data": {
                        "current_status": order.patient_acceptance_status,
                        "timestamp": order.patient_acceptance_timestamp
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            # Update order status
            if action == "ACCEPT":
                order.patient_acceptance_status = AssessmentOrder.ACCEPTANCE_ACCEPTED
                message = "Accepted"
                event_type = "ORDER_ACCEPTED_BY_DOCTOR"
            else:  # REJECT
                order.patient_acceptance_status = AssessmentOrder.ACCEPTANCE_REJECTED
                message = "Rejected"
                event_type = "ORDER_REJECTED_BY_DOCTOR"

            order.patient_acceptance_timestamp = timezone.now()
            order.patient_acceptance_notes = notes if notes else None
            order.save(update_fields=[
                "patient_acceptance_status",
                "patient_acceptance_timestamp",
                "patient_acceptance_notes"
            ])

            # Log audit event
            log_event(
                org=order.org,
                event_type=event_type,
                entity_type="AssessmentOrder",
                entity_id=order.id,
                actor_role="Doctor",
                details={
                    "action": action,
                    "notes": notes,
                    "patient_name": order.patient.full_name,
                    "battery_code": order.battery_code
                },
                request=request,
                severity="INFO"
            )

            response = Response({
                "success": True,
                "message": message,
                "data": {
                    "order_id": order.id,
                    "patient_acceptance_status": order.patient_acceptance_status,
                    "patient_acceptance_timestamp": order.patient_acceptance_timestamp.isoformat() if order.patient_acceptance_timestamp else None,
                    "public_token": new_token
                }
            }, status=status.HTTP_200_OK)

            # Return rotated token in header
            response["X-Public-Token"] = new_token

            return response

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
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in PatientAcceptRejectOrder: {str(e)}", exc_info=True)

            return Response({
                "success": False,
                "message": "Unable to process your request at this time.",
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
