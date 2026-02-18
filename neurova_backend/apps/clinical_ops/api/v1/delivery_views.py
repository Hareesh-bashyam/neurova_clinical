import logging

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone

from common.encryption_decorators import decrypt_request, encrypt_response

from apps.clinical_ops.models import AssessmentOrder
from apps.clinical_ops.audit.logger import log_event


logger = logging.getLogger(__name__)


class SetDeliveryAndMarkDelivered(APIView):
    permission_classes = [IsAuthenticated]

    @decrypt_request
    @encrypt_response
    def post(self, request):
        try:
            org = request.user.profile.organization  
    
            order_id = request.decrypted_data.get("order_id")
            delivery_mode = request.decrypted_data.get("delivery_mode")
            delivery_target = request.decrypted_data.get("delivery_target")
    
            if not all([order_id, delivery_mode]):
                return Response(
                    {
                        "success": False,
                        "message": "Order id and delivery mode are required",
                        "data": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
    
            order = get_object_or_404(
                AssessmentOrder,
                id=order_id,
                org=org,
                deletion_status="ACTIVE",
            )
    
            # 🔒 Lifecycle guard
            if order.status not in {
                AssessmentOrder.STATUS_COMPLETED,
                AssessmentOrder.STATUS_AWAITING_REVIEW,
            }:
                return Response(
                    {
                        "success": False,
                        "message": f"Cannot Deliver Order in status {order.status}",
                        "data": None,
                    },
                    status=status.HTTP_409_CONFLICT,
                )
    
            order.delivery_mode = delivery_mode
            order.delivery_target = delivery_target
            order.status = AssessmentOrder.STATUS_DELIVERED
            order.delivered_at = timezone.now()
    
            order.save(
                update_fields=[
                    "delivery_mode",
                    "delivery_target",
                    "status",
                    "delivered_at",
                ]
            )

            # Audit log for delivery
            log_event(
                org=org,
                event_type="ORDER_DELIVERED",
                entity_type="AssessmentOrder",
                entity_id=order.id,
                actor_user_id=str(request.user.id),
                actor_name=request.user.username,
                actor_role=request.user.profile.role,
                request=request,
                severity="INFO",
                details={
                    "delivery_mode": delivery_mode,
                    "delivery_target": delivery_target
                }
            )
    
            return Response(
                {
                    "success": True,
                    "message": "Report Delivered Successfully",
                    "data": {
                        "order_id": order.id,
                        "status": order.status,
                        "delivery_mode": order.delivery_mode,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error delivering order: {str(e)}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "message": "Unable to deliver order at this time.",
                    "data": None,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
