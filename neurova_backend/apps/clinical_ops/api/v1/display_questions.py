from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import AnonRateThrottle
from rest_framework.exceptions import PermissionDenied

from apps.clinical_ops.services.public_token_validator import validate_and_rotate_url_token
from apps.clinical_ops.audit.logger import log_event
from apps.clinical_ops.battery_assessment_model import BatteryAssessment, Battery


class PublicQuestionDisplay(APIView):
    authentication_classes = []
    permission_classes = []
    throttle_classes = [AnonRateThrottle]

    def get(self, request, token):

        try:
            # Validate & Rotate Token
            order, new_token = validate_and_rotate_url_token(token, request)

            # Resolve battery
            battery = get_object_or_404(
                Battery,
                battery_code=order.battery_code,
                is_active=True
            )

            # Fetch ordered assessments
            battery_tests = (
                BatteryAssessment.objects
                .filter(
                    battery=battery,
                    assessment__is_active=True
                )
                .select_related("assessment")
                .order_by("display_order")
            )

            tests_payload = []

            for bt in battery_tests:
                assessment = bt.assessment
                questions = assessment.questions_json.get("questions", [])

                tests_payload.append({
                    "test_code": assessment.test_code,
                    "title": assessment.title,
                    "version": assessment.version,
                    "description": assessment.description,
                    "questions": questions,
                })

            # Audit Log
            log_event(
                org=order.org,
                event_type="QUESTIONS_VIEWED",
                entity_type="AssessmentOrder",
                entity_id=order.id,
                actor_role="Patient",
                request=request,
                severity="INFO"
            )

            response = Response(
                {
                    "success": True,
                    "data": {
                        "order_id": order.id,
                        "battery": {
                            "battery_code": battery.battery_code,
                            "name": battery.name,
                            "version": battery.version,
                            "screening_label": battery.screening_label,
                            "signoff_required": battery.signoff_required,
                        },
                        "tests": tests_payload
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
                    "message": "Unable to retrieve questions at this time.",
                    "data": None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
