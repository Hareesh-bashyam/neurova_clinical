# orders/views.py

from django.utils.timezone import now

from rest_framework.views import APIView
from rest_framework.response import Response

from common.permissions import IsStaff
from catalog.models import Panel
from auditlogs.utils import log_event
from .models import Order
from sessions.models import Session


class OrderCreateView(APIView):
    permission_classes = [IsStaff]

    def post(self, request):
        order = Order.objects.create(
            organization=request.user.profile.organization,
            patient_id=request.data["patient_id"],
            panel=Panel.objects.get(
                code=request.data["panel_code"],
                organization=request.user.profile.organization,
            ),
        )

        log_event(
            request,
            order.organization,
            "ORDER_CREATED",
            "Order",
            order.id,
        )

        return Response({"order_id": order.id})


class StartSessionView(APIView):
    permission_classes = [IsStaff]

    def post(self, request, order_id):
        order = Order.objects.get(
            id=order_id,
            organization=request.user.profile.organization,
        )

        session = Session.objects.create(
            organization=order.organization,
            order=order,
            status="STARTED",
            started_at=now(),
        )

        order.status = "IN_PROGRESS"
        order.save(update_fields=["status"])

        log_event(
            request,
            order.organization,
            "SESSION_STARTED",
            "Session",
            session.id,
        )

        return Response({"session_id": session.id})
