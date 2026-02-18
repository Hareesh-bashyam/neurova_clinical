from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone

from common.encryption_decorators import decrypt_request, encrypt_response

from apps.clinical_ops.models import AssessmentOrder


class SetDeliveryAndMarkDelivered(APIView):
    permission_classes = [IsAuthenticated]

    @decrypt_request
    @encrypt_response
    def post(self, request):
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
