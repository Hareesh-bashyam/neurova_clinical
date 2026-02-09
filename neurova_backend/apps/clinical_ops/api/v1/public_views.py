from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.clinical_ops.models import AssessmentOrder
from rest_framework.throttling import AnonRateThrottle

class PublicOrderBootstrap(APIView):
    authentication_classes = []
    permission_classes = []
    throttle_classes = [AnonRateThrottle]

    def get(self, request, token):
        order = get_object_or_404(AssessmentOrder, public_token=token)

        if order.public_link_expires_at and timezone.now() > order.public_link_expires_at:
            return Response({"success": False,
                            "message":"Link Expired", 
                            "data": None}, status=403)

        # Mark started if not started
        if order.status == AssessmentOrder.STATUS_IN_PROGRESS:
            order.mark_started()

        return Response(
            {
                "success": True,
                "message": "Order initialized successfully",
                "data": {
                    "org_id": order.org.id,
                    "order_id": order.id,
                    "patient_id": order.patient.id,
                    "patient_name": order.patient.full_name,
                    "patient_age": order.patient.age, 
                    "patient_gender": order.patient.sex,
                    "battery_code": order.battery_code,
                    "battery_version": order.battery_version,
                    "status": order.status,
                },
            },
            status=status.HTTP_200_OK,
        )

