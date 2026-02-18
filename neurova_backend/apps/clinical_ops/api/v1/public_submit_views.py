from django.utils import timezone
from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import AnonRateThrottle
from rest_framework.exceptions import PermissionDenied

from common.encryption_decorators import decrypt_request, encrypt_response

from apps.clinical_ops.models import AssessmentOrder, ResponseQuality
from apps.clinical_ops.models_assessment import AssessmentResponse, AssessmentResult
from apps.clinical_ops.services.quality import compute_quality
from apps.clinical_ops.services.scoring_adapter import score_battery
from apps.clinical_ops.services.public_token_validator import validate_and_rotate_url_token
from apps.clinical_ops.audit.logger import log_event


class PublicOrderSubmit(APIView):
    authentication_classes = []
    permission_classes = []
    throttle_classes = [AnonRateThrottle]

    @decrypt_request
    @encrypt_response
    @transaction.atomic
    def post(self, request, token):

        try:
            # Validate & Rotate Token
            order, new_token = validate_and_rotate_url_token(token, request)

            # Lock order row safely
            order = (
                AssessmentOrder.objects
                .select_for_update()
                .get(id=order.id)
            )

            # Ensure order is in progress
            if order.status != AssessmentOrder.STATUS_IN_PROGRESS:
                return Response(
                    {
                        "success": False,
                        "status": order.status,
                        "message": "Order not in progress",
                        "data": None
                    },
                    status=status.HTTP_409_CONFLICT
                )

            # Deduplication
            if hasattr(order, "assessmentresponse"):
                return Response(
                    {
                        "success": True,
                        "message": "Duplicate submission ignored",
                        "data": {"order_id": order.id}
                    },
                    status=status.HTTP_200_OK
                )

            answers = request.decrypted_data.get("answers")
            duration_seconds = int(request.decrypted_data.get("duration_seconds", 0))

            if not isinstance(answers, list) or not answers:
                return Response(
                    {
                        "success": False,
                        "message": "Answers required",
                        "data": None
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Save raw answers
            response_obj = AssessmentResponse.objects.create(
                org=order.org,
                order=order,
                answers_json={"answers": answers},
                duration_seconds=duration_seconds,
                submitted_at=timezone.now(),
            )

            # Compute response quality
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

            # Score full battery
            result_payload = score_battery(
                battery_code=order.battery_code,
                battery_version=order.battery_version,
                answers_json=response_obj.answers_json,
            )

            AssessmentResult.objects.create(
                org=order.org,
                order=order,
                result_json=result_payload,
                primary_severity=result_payload["summary"]["primary_severity"],
                has_red_flags=result_payload["summary"]["has_red_flags"],
            )

            # Finalize order
            order.mark_completed()

            # Audit log
            log_event(
                org=order.org,
                event_type="ASSESSMENT_SUBMITTED",
                entity_type="AssessmentOrder",
                entity_id=order.id,
                actor_role="Patient",
                request=request,
                severity="INFO"
            )

            response = Response(
                {
                    "success": True,
                    "message": "Assessment submitted successfully",
                    "data": {
                        "order_id": order.id,
                        
                    }
                },
                status=status.HTTP_200_OK
            )

            # Return rotated token
            response["X-Public-Token"] = new_token

            return response

        except PermissionDenied as e:
            return Response(
                {
                    "success": False,
                    "message": str(e),
                    "data": None
                },
                status=status.HTTP_403_FORBIDDEN
            )

        except Exception:
            return Response(
                {
                    "success": False,
                    "message": "Unable to submit assessment at this time.",
                    "data": None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
