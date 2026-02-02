from django.utils import timezone
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import AnonRateThrottle

from apps.clinical_ops.models import AssessmentOrder, ResponseQuality
from apps.clinical_ops.models_assessment import AssessmentResponse, AssessmentResult
from apps.clinical_ops.services.quality import compute_quality
from apps.clinical_ops.services.scoring_adapter import score_battery


class PublicOrderSubmit(APIView):
    authentication_classes = []
    permission_classes = []
    throttle_classes = [AnonRateThrottle]

    @transaction.atomic
    def post(self, request, token):
        # 🔒 Lock order
        order = (
            AssessmentOrder.objects
            .select_for_update()
            .get(public_token=token)
        )

        if order.status != AssessmentOrder.STATUS_IN_PROGRESS:
            return Response(
                {
                    "success": False,
                    "message": "Order not in progress",
                    "data": None
                },
                status=status.HTTP_409_CONFLICT
            )

        if order.public_link_expires_at and timezone.now() > order.public_link_expires_at:
            return Response(
                {
                    "success": False,
                    "message": "Link expired",
                    "data": None
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # 🔁 Deduplication
        if hasattr(order, "response"):
            return Response(
                {
                    "success": True,
                    "message": "Duplicate submission ignored",
                    "data": {"order_id": order.id}
                },
                status=status.HTTP_200_OK
            )

        answers = request.data.get("answers")
        duration_seconds = int(request.data.get("duration_seconds", 0))

        if not isinstance(answers, list) or not answers:
            return Response(
                {
                    "success": False,
                    "message": "Answers required",
                    "data": None
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Save raw answers
        response = AssessmentResponse.objects.create(
            org=order.org,
            order=order,
            answers_json={"answers": answers},
            duration_seconds=duration_seconds,
            submitted_at=timezone.now(),
        )

        # ✅ Compute response quality (DICT!)
        quality = compute_quality(
            answers=answers,
            duration_seconds=duration_seconds
        )

        ResponseQuality.objects.create(
            org=order.org,
            order=order,
            duration_seconds=duration_seconds,
            straight_lining_flag=quality["straight_lining_flag"],
            too_fast_flag=quality["too_fast_flag"],
            inconsistency_flag=quality["inconsistency_flag"],
            notes=quality.get("notes"),
        )

        # ✅ Score full battery (MULTI TEST SAFE)
        result_payload = score_battery(
            battery_code=order.battery_code,
            battery_version=order.battery_version,
            answers_json=response.answers_json,
        )

        AssessmentResult.objects.create(
            org=order.org,
            order=order,
            result_json=result_payload,
            primary_severity=result_payload["summary"]["primary_severity"],
            has_red_flags=result_payload["summary"]["has_red_flags"],
        )

        # ✅ Finalize order
        order.mark_completed()

        return Response(
            {
                "success": True,
                "message": "Assessment submitted successfully",
                "data": {
                    "order_id": order.id
                }
            },
            status=status.HTTP_200_OK
        )
