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


class PublicOrderSubmit(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, token):
        """
        Expected payload:
        {
          "duration_seconds": 420,
          "answers": [ {"question_id":"phq9_q1","value":2}, ... ],
          "meta": {"device":"tablet","lang":"en"}
        }
        """
        order = get_object_or_404(AssessmentOrder, public_token=token)

        # expiry check
        if order.public_link_expires_at and timezone.now() > order.public_link_expires_at:
            return Response({"error": "link_expired"}, status=403)

        # 🔒 Consent required before answers submission
        if not ConsentRecord.objects.filter(order=order).exists():
            return Response({"error": "consent_required"}, status=403)

        duration_seconds = int(request.data.get("duration_seconds") or 0)
        answers = request.data.get("answers") or []
        meta = request.data.get("meta") or {}

        if not isinstance(answers, list) or len(answers) == 0:
            return Response({"error": "answers_required"}, status=400)

        # store raw answers
        answers_json = {"answers": answers, "meta": meta}

        AssessmentResponse.objects.update_or_create(
            org_id=order.org_id,
            order=order,
            defaults={
                "answers_json": answers_json,
                "duration_seconds": duration_seconds,
                "submitted_at": timezone.now(),
            }
        )

        # quality flags
        q = compute_quality(duration_seconds=duration_seconds, answers=answers)
        ResponseQuality.objects.update_or_create(
            org_id=order.org_id,
            order=order,
            defaults=q
        )

        # mark completed
        order.mark_completed()

        # compute result via scoring engine
        result_json = score_battery(
            battery_code=order.battery_code,
            battery_version=order.battery_version,
            answers_json=answers_json
        )

        # 🔒 Normalize result_json for compliance BEFORE signoff
        summary = result_json.get("summary", {})
        if "has_red_flags" not in summary:
            summary["has_red_flags"] = False
        result_json["summary"] = summary

        primary_severity = summary.get("primary_severity")
        has_red_flags = bool(summary.get("has_red_flags", False))

        AssessmentResult.objects.update_or_create(
            org_id=order.org_id,
            order=order,
            defaults={
                "result_json": result_json,
                "primary_severity": primary_severity,
                "has_red_flags": has_red_flags,
                "computed_at": timezone.now(),
            }
        )

        # move to awaiting review (clinic workflow)
        order.status = AssessmentOrder.STATUS_AWAITING_REVIEW
        order.save(update_fields=["status"])

        return Response({
            "ok": True,
            "order_id": order.id,
            "status": order.status,
            "primary_severity": primary_severity,
            "has_red_flags": has_red_flags
        }, status=status.HTTP_200_OK)
