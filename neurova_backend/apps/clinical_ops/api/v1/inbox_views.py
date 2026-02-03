from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.clinical_ops.models import AssessmentOrder


class ClinicalInboxView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = request.user.profile.organization

        orders = (
            AssessmentOrder.objects
            .filter(
                org=org,
                deletion_status="ACTIVE",
                status=AssessmentOrder.STATUS_COMPLETED,
            )
            .select_related("patient", "result")
            .order_by("-created_at")[:200]
        )

        results = []

        for order in orders:
            result = getattr(order, "result", None)

            results.append({
                "order_id": order.id,
                "patient_name": order.patient.full_name,
                "age": order.patient.age,
                "sex": order.patient.sex,
                "battery_code": order.battery_code,
                "created_at": order.created_at,
                "status": order.status,  # always COMPLETED
                "primary_severity": result.primary_severity if result else None,
                "has_red_flags": result.has_red_flags if result else False,
            })

        return Response(
            {
                "success": True,
                "data": {
                    "results": results
                }
            },
            status=status.HTTP_200_OK
        )
