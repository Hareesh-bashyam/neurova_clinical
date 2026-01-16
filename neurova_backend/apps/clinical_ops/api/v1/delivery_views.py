from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from apps.clinical_ops.models import AssessmentOrder, Org

class SetDeliveryAndMarkDelivered(APIView):
    def post(self, request):
        org_id = request.data.get("org_id")
        order_id = request.data.get("order_id")
        delivery_mode = request.data.get("delivery_mode")
        delivery_target = request.data.get("delivery_target")

        if not all([org_id, order_id, delivery_mode]):
            return Response({"error":"org_id, order_id, delivery_mode required"}, status=400)

        org = get_object_or_404(Org, id=org_id, is_active=True)
        order = get_object_or_404(AssessmentOrder, id=order_id, org=org)

        order.delivery_mode = delivery_mode
        order.delivery_target = delivery_target

        order.status = AssessmentOrder.STATUS_DELIVERED
        order.delivered_at = timezone.now()
        order.save(update_fields=["delivery_mode","delivery_target","status","delivered_at"])

        return Response({"ok": True, "status": order.status}, status=status.HTTP_200_OK)
