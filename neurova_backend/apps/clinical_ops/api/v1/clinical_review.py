from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from common.encryption_decorators import encrypt_response

from apps.clinical_ops.models import AssessmentOrder
from apps.clinical_ops.models_assessment import AssessmentResult
from apps.clinical_ops.models_report import AssessmentReport


BATTERY_TEST_LABELS = {
    "PHQ9": "Mood Assessment",
    "GAD7": "Anxiety Screening",
    "STOP_BANG": "Sleep Quality",
    "PSS10": "Stress Evaluation",
    "AUDIT": "Alcohol Use",
    "MDQ": "Mood Disorder Screening",
}


class ClinicalReviewDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @encrypt_response
    def get(self, request, order_id):
        org = request.user.profile.organization

        order = get_object_or_404(
            AssessmentOrder,
            id=order_id,
            org=org,
            deletion_status="ACTIVE"
        )

        result = getattr(order, "result", None)
        report = getattr(order, "report", None)

        result_json = result.result_json if result else {}
        per_test = result_json.get("per_test", {})

        # -------------------------------
        # Battery Summary
        # -------------------------------
        battery_items = []
        for test_code, label in BATTERY_TEST_LABELS.items():
            battery_items.append({
                "label": label,
                "test_code": test_code,
                "status": "COMPLETED" if test_code in per_test else "NOT_ATTEMPTED"
            })

        # -------------------------------
        # Clinical Flag
        # -------------------------------
        red_flags_value = result_json.get("summary", {}).get("red_flags", [])
        has_red_flags = bool(
            result and result.has_red_flags
        )

        # -------------------------------
        # Audit Timeline
        # -------------------------------
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

        return Response(
            {
                "success": True,
                "message": "Assessment Review Details",
                "data": {
                    "header": {
                        "org_name": org.name
                    },

                    "patient_summary": {
                        "name": order.patient.full_name,
                        "age": order.patient.age,
                        "sex": order.patient.sex,
                        "hospital_id": order.patient.mrn,
                        "assessment_date": order.completed_at.strftime("%B %d, %Y")
                        if order.completed_at else None
                    },

                    "battery_summary": {
                        "items": battery_items
                    },

                    "clinical_flag": {
                        "visible": has_red_flags,
                        "type": "WARNING",
                        "title": "Clinical Flag",
                        "red_flags":red_flags_value,
                        "message": (
                            "Suicide ideation item endorsed: Yes"
                            if has_red_flags else None
                        )
                    },

                    "audit_timeline": timeline,

                }
            },
            status=status.HTTP_200_OK
        )



# from django.shortcuts import get_object_or_404
# from django.utils import timezone
# from rest_framework.views import APIView
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from rest_framework import status

# from apps.clinical_ops.models import AssessmentOrder, Battery


# class ClinicalReviewDetailView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, order_id):
#         org = request.user.profile.organization

#         order = get_object_or_404(
#             AssessmentOrder,
#             id=order_id,
#             org=org,
#             deletion_status="ACTIVE"
#         )

#         # ----------------------------------
#         # Battery (IMPORTANT FIX)
#         # ----------------------------------
#         battery = get_object_or_404(
#             Battery,
#             battery_code=order.battery_code,
#             is_active=True
#         )

#         result = getattr(order, "result", None)
#         report = getattr(order, "report", None)

#         result_json = result.result_json if result else {}
#         per_test = result_json.get("per_test", {})

#         # ----------------------------------
#         # Battery Summary (tests)
#         # ----------------------------------
#         battery_items = []
#         for test in battery.battery_tests.select_related("assessment").all():
#             assessment = test.assessment
#             battery_items.append({
#                 "label": assessment.title,
#                 "test_code": assessment.test_code,
#                 "status": "COMPLETED"
#                 if assessment.test_code in per_test
#                 else "NOT_ATTEMPTED"
#             })

#         # ----------------------------------
#         # Clinical Flag
#         # ----------------------------------
#         has_red_flags = bool(result and result.has_red_flags)

#         # ----------------------------------
#         # Audit Timeline
#         # ----------------------------------
#         timeline = []

#         if order.started_at:
#             timeline.append({
#                 "label": "Assessment Started",
#                 "time": timezone.localtime(order.started_at).strftime("%I:%M %p")
#             })

#         if order.completed_at:
#             timeline.append({
#                 "label": "Assessment Completed",
#                 "time": timezone.localtime(order.completed_at).strftime("%I:%M %p")
#             })

#         if report and report.generated_at:
#             timeline.append({
#                 "label": "Report Generated",
#                 "time": timezone.localtime(report.generated_at).strftime("%I:%M %p")
#             })

#         # ----------------------------------
#         # FINAL RESPONSE
#         # ----------------------------------
#         return Response(
#             {
#                 "success": True,
#                 "message": "Assessment Review Details",
#                 "data": {

#                     # ✅ PANEL SUMMARY (FIXED)
#                     "panel_summary": {
#                         "battery_code": battery.battery_code,
#                         "battery_name": battery.name,
#                         "battery_description": battery.screening_label,
#                     },

#                     "patient_summary": {
#                         "name": order.patient.full_name,
#                         "age": order.patient.age,
#                         "sex": order.patient.sex,
#                         "hospital_id": order.patient.mrn,
#                         "assessment_date": (
#                             order.completed_at.strftime("%B %d, %Y")
#                             if order.completed_at else None
#                         )
#                     },

#                     "battery_summary": {
#                         "items": battery_items
#                     },

#                     "clinical_flag": {
#                         "visible": has_red_flags,
#                         "type": "WARNING" if has_red_flags else "NONE",
#                         "title": "Clinical Flag" if has_red_flags else None,
#                         "message": (
#                             "Responses indicate elevated distress markers requiring clinical attention."
#                             if has_red_flags else None
#                         )
#                     },

#                     "audit_timeline": timeline,
#                 }
#             },
#             status=status.HTTP_200_OK
#         )
