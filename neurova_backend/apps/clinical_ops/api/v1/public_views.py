from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.clinical_ops.models import AssessmentOrder

class PublicOrderBootstrap(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, token):
        order = get_object_or_404(AssessmentOrder, public_token=token)

        if order.public_link_expires_at and timezone.now() > order.public_link_expires_at:
            return Response({"error":"link_expired"}, status=403)

        # Mark started if not started
        if order.status == AssessmentOrder.STATUS_CREATED:
            order.mark_started()

        return Response({
            "order_id": order.id,
            "battery_code": order.battery_code,
            "battery_version": order.battery_version,
            "status": order.status,
        }, status=status.HTTP_200_OK)
