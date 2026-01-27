from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.clinical_ops.models import AssessmentOrder
from apps.clinical_ops.models_assessment import AssessmentResponse, AssessmentResult
from apps.clinical_ops.models import ResponseQuality
from apps.clinical_ops.models_consent import ConsentRecord

from apps.clinical_ops.services.quality import compute_quality
from apps.clinical_ops.services.scoring_adapter import score_battery
from rest_framework.throttling import AnonRateThrottle
from django.db import transaction

class PublicOrderSubmit(APIView):
    authentication_classes = []
    permission_classes = []
    throttle_classes = [AnonRateThrottle]

    @transaction.atomic
    def post(self, request, token):
        # 🔒 Lock order row
        order = (
            AssessmentOrder.objects
            .select_for_update()
            .get(public_token=token)
        )

        if order.status != AssessmentOrder.STATUS_IN_PROGRESS:
            return Response(
                {"error": "order_not_in_progress"},
                status=status.HTTP_409_CONFLICT,
            )

        if order.public_link_expires_at and timezone.now() > order.public_link_expires_at:
            return Response(
                {"error": "link_expired"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # 🔁 STEP 7 — IDEMPOTENCY GUARD
        idem_key = request.headers.get("X-Idempotency-Key")
        if idem_key:
            obj, created = IdempotencyKey.objects.get_or_create(
                session=order.session,
                key=idem_key,
            )
            if not created:
                return Response(
                    {
                        "ok": True,
                        "deduped": True,
                        "message": "Duplicate submission ignored",
                    },
                    status=status.HTTP_200_OK,
                )

        answers = request.data.get("answers") or []
        if not isinstance(answers, list) or not answers:
            return Response(
                {"error": "answers_required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 🔁 Existing safety (keep this!)
        if hasattr(order, "assessmentresponse"):
            return Response(
                {"ok": True, "deduped": True},
                status=status.HTTP_200_OK,
            )

        answers_json = {"answers": answers}

        AssessmentResponse.objects.create(
            order=order,
            org=order.org,
            answers_json=answers_json,
            submitted_at=timezone.now(),
        )

        order.status = AssessmentOrder.STATUS_COMPLETED
        order.save(update_fields=["status"])

        return Response(
            {"ok": True},
            status=status.HTTP_200_OK,
        )