from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.clinical_ops.models import (
    AssessmentOrder,
    Battery,
    BatteryAssessment,
)
from apps.clinical_ops.models_assessment import AssessmentResult
from apps.clinical_ops.models_report import AssessmentReport


class ClinicalReviewDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        org = request.user.profile.organization

        # -----------------------------
        # Order
        # -----------------------------
        order = get_object_or_404(
            AssessmentOrder,
            id=order_id,
            org=org,
            deletion_status="ACTIVE",
        )

        result: AssessmentResult | None = getattr(order, "result", None)
        report: AssessmentReport | None = getattr(order, "report", None)

        result_json = result.result_json if result else {}
        per_test = result_json.get("per_test", {})

        # -----------------------------
        # Battery (from DB)
        # -----------------------------
        battery = get_object_or_404(
            Battery,
            battery_code=order.battery_code,
            is_active=True,
        )

        battery_tests = (
            BatteryAssessment.objects
            .select_related("assessment")
            .filter(battery=battery)
            .order_by("display_order")
        )

        test_components = []
        for bt in battery_tests:
            assessment = bt.assessment
            test_components.append({
                "test_code": assessment.test_code,
                "label": assessment.title,
                "status": (
                    "COMPLETED"
                    if assessment.test_code in per_test
                    else "NOT_ATTEMPTED"
                )
            })

        # -----------------------------
        # Panel Summary (Clinical Flag)
        # -----------------------------
        panel_summary = {
            "visible": False,
            "severity": None,
            "title": None,
            "items": []
        }

        if result and result.has_red_flags:
            panel_summary = {
                "visible": True,

                "items": result.red_flag_summary or []
            }

        # -----------------------------
        # Audit Timeline
        # -----------------------------
        timeline = []

        if order.started_at:
            timeline.append({
                "label": "Assessment Started",
                "time": timezone.localtime(order.started_at).strftime("%I:%M %p")
            })

        if order.completed_at:
            timeline.append({
                "label": "Assessment Completed",
                "time": timezone.localtime(order.completed_at).strftime("%I:%M %p")
            })

        if report and report.generated_at:
            timeline.append({
                "label": "Report Generated",
                "time": timezone.localtime(report.generated_at).strftime("%I:%M %p")
            })

        # -----------------------------
        # Response
        # -----------------------------
        return Response(
            {
                "success": True,
                "message": "Clinical Review Details",
                "data": {
                    "header": {
                        "org_name": org.name
                    },

                    "patient_summary": {
                        "name": order.patient.full_name,
                        "age": order.patient.age,
                        "sex": order.patient.sex,
                        "hospital_id": order.patient.mrn,
                        "assessment_date": (
                            order.completed_at.strftime("%B %d, %Y")
                            if order.completed_at else None
                        )
                    },

                    "battery_summary": {
                        "battery_code": battery.battery_code,
                        "name": battery.name,
                        "version": battery.version,
                        "screening_label": battery.screening_label,
                        "signoff_required": battery.signoff_required
                    },

                    "panel_summary": panel_summary,

                    "test_components": test_components,

                    "audit_timeline": timeline,
                }
            },
            status=status.HTTP_200_OK
        )
