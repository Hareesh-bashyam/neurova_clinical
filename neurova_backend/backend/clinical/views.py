from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

from django.utils import timezone
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.http import HttpResponse

from common.permissions import IsClinician
from rest_framework.permissions import AllowAny

from backend.clinical.models import (
    ClinicalOrder,
    BatterySession,
    TestRun,
)

from backend.clinical.batteries.battery_runner import (
    start_session,
    get_current_test_code,
    open_current_test_run,
    advance_to_next_test,
    get_battery_def,
)

from backend.clinical.audit.services import audit
from backend.clinical.constants import ORDER_STATUS_FLOW

from backend.clinical.reporting.generate import generate_report_for_order_v1
from backend.clinical.reporting.pdf_renderer_v1 import render_pdf_from_report_json_v1

from backend.clinical.security.org_guard import (
    get_request_org_id,
    require_org_match,
)

from reports.models import ClinicalReport
from backend.clinical.models import IdempotencyKey



VALID_GENDERS = {"MALE", "Male", "male", "Female", "female", "FEMALE", "OTHER"}
MIN_AGE = 1
MAX_AGE = 120


# -------------------------------------------------
# 6.1 CREATE ORDER
# -------------------------------------------------
class ClinicalOrderCreateView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        data = request.data

        required = [
            "organization_id",
            "patient_name",
            "encounter_type",
            "administration_mode",
            "battery_code",
        ]
        for field in required:
            if field not in data:
                return Response(
                    {"success": False, "message": f"Missing field: {field}", "data": None},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        gender = data.get("patient_gender")
        if gender is not None and gender not in VALID_GENDERS:
            return Response(
                {
                    "success": False,
                    "message": "Invalid patient_gender. Allowed: MALE, FEMALE, OTHER",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        age = data.get("patient_age")
        if age is not None:
            try:
                age = int(age)
            except (TypeError, ValueError):
                return Response(
                    {"success": False, "message": "patient_age must be an integer", "data": None},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if age < MIN_AGE or age > MAX_AGE:
                return Response(
                    {
                        "success": False,
                        "message": "patient_age must be between 1 and 120",
                        "data": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        get_battery_def(data["battery_code"])

        order = ClinicalOrder.objects.create(
            organization_id=data["organization_id"],
            patient_name=data["patient_name"],
            patient_age=age,
            patient_gender=gender,
            encounter_type=data["encounter_type"],
            administration_mode=data["administration_mode"],
            battery_code=data["battery_code"],
            battery_version="1.0",
            status="CREATED",
        )

        session = BatterySession.objects.create(
            organization_id=order.organization_id,
            order=order,
            status="NOT_STARTED",
        )

        return Response(
            {
                "success": True,
                "message": "Order created successfully",
                "data": {
                    "order_id": str(order.id),
                    "session_id": str(session.id),
                    "battery_code": order.battery_code,
                },
            },
            status=status.HTTP_201_CREATED,
        )



# -------------------------------------------------
# 6.2 START SESSION
# -------------------------------------------------
class StartSessionView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, session_id):
        session = get_object_or_404(BatterySession, id=session_id)

        if session.status not in ["READY", "NOT_STARTED"]:
            return Response(
                {"success": False, "message": "Session cannot be started", "data": None},
                status=status.HTTP_409_CONFLICT,
            )

        start_session(session)

        test_code = get_current_test_code(session)
        battery = get_battery_def(session.order.battery_code)

        return Response(
            {
                "success": True,
                "message": "Session started successfully",
                "data": {
                    "session_id": str(session.id),
                    "current_test_index": session.current_test_index,
                    "test_code": test_code,
                    "screening_label": battery["screening_label"],
                },
            },
            status=status.HTTP_200_OK,
        )


# -------------------------------------------------
# 6.3 GET CURRENT TEST
# -------------------------------------------------
class GetCurrentTestView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, session_id):
        session = get_object_or_404(BatterySession, id=session_id)

        if session.status != "IN_PROGRESS":
            return Response(
                {"success": False, "message": "Session is not in progress", "data": None},
                status=status.HTTP_409_CONFLICT,
            )

        test_code = get_current_test_code(session)
        battery = get_battery_def(session.order.battery_code)

        return Response(
            {
                "success": True,
                "message": "Current test retrieved successfully",
                "data": {
                    "session_id": str(session.id),
                    "current_test_index": session.current_test_index,
                    "test_code": test_code,
                    "screening_label": battery["screening_label"],
                },
            },
            status=status.HTTP_200_OK,
        )


# -------------------------------------------------
# 6.4 SUBMIT CURRENT TEST
# -------------------------------------------------
class SubmitCurrentTestView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request, session_id):
        # 🔒 HARD LOCK SESSION ROW (STEP 6)
        session = (
            BatterySession.objects
            .select_for_update()
            .get(id=session_id)
        )

        # 🔁 IDEMPOTENCY GUARD (STEP 7)
        idem_key = request.headers.get("X-Idempotency-Key")
        if idem_key:
            obj, created = IdempotencyKey.objects.get_or_create(
                session=session,
                key=idem_key,
            )
            if not created:
                return Response(
                    {
                        "success": True,
                        "message": "Duplicate submission ignored",
                        "data": {
                            "deduped": True,
                            "session_id": str(session.id),
                            "current_test_index": session.current_test_index,
                            "request_id": getattr(request, "request_id", None),
                        },
                    },
                    status=status.HTTP_200_OK,
                )

        # ---- SESSION STATE VALIDATION ----
        if session.status != "IN_PROGRESS":
            return Response(
                {
                    "success": False,
                    "message": "Session not in progress",
                    "data": None,
                },
                status=status.HTTP_409_CONFLICT,
            )

        # ---- EXPECTED TEST VALIDATION ----
        expected_test_code = get_current_test_code(session)
        submitted_test_code = request.data.get("test_code")

        # 🔒 SECURITY FIX: Require test_code to prevent playback/misalignment attacks
        if not submitted_test_code:
            return Response(
                {
                    "success": False,
                    "message": "test_code is required for integrity check",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if submitted_test_code != expected_test_code:
            return Response(
                {
                    "success": False,
                    "message": "Invalid test submission order",
                    "data": {
                        "expected_test_code": expected_test_code,
                        "submitted_test_code": submitted_test_code,
                    },
                },
                status=status.HTTP_409_CONFLICT,
            )

        # ---- OPEN / FETCH TEST RUN ----
        test_run = open_current_test_run(session)

        # ---- DUPLICATE SUBMISSION SAFETY (LEGACY) ----
        if test_run.time_submitted is not None:
            return Response(
                {
                    "success": True,
                    "message": "Test already submitted",
                    "data": None,
                },
                status=status.HTTP_200_OK,
            )

        # ---- SAVE ANSWERS ----
        test_run.raw_responses = request.data.get("raw_responses")
        test_run.time_submitted = timezone.now()
        test_run.save(update_fields=["raw_responses", "time_submitted"])

        # ---- ADVANCE SESSION ----
        has_next = advance_to_next_test(session)
        
        next_test_code = None
        if has_next:
             session.refresh_from_db()
             next_test_code = get_current_test_code(session)

        if not has_next:
            session.status = "COMPLETED"
            session.completed_at = timezone.now()
            session.save(update_fields=["status", "completed_at"])

            # ✅ ALSO COMPLETE ORDER (THIS WAS MISSING)
            order = session.order
            order.status = "COMPLETED"
            order.save(update_fields=["status"])

        return Response(
                {
                    "success": True,
                    "message": "Test submitted successfully",
                    "data": {
                        "completed": not has_next,
                        "next_test_code": next_test_code,
                        "next_test_index": session.current_test_index,
                    },
                },
                status=status.HTTP_200_OK,
            )

# -------------------------------------------------
# 6.5 GENERATE REPORT (PHASE 1)
# -------------------------------------------------
class GenerateReportView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request, order_id):
        order = get_object_or_404(ClinicalOrder, id=order_id)

        # ---- STEP 1: order must be completed ----
        if order.status != "COMPLETED":
            return Response(
                {
                    "success": False,
                    "message": "Order not completed",
                    "data": None,
                },
                status=status.HTTP_409_CONFLICT,
            )

        # ---- STEP 2: generate report ----
        report = generate_report_for_order_v1(order)

        # ---- STEP 3: PHASE 1 explicit lifecycle ----
        report.validation_status = ClinicalReport.DATA_VALIDATED
        report.review_status = ClinicalReport.REVIEW_DRAFT
        report.save(update_fields=["validation_status", "review_status"])

        return Response(
            {
                "success": True,
                "message": "Report generated successfully",
                "data": {
                    "report_id": str(report.id),
                },
            },
            status=status.HTTP_200_OK,
        )

# -------------------------------------------------
# ORDER STATUS UPDATE
# -------------------------------------------------
class ClinicalOrderStatusUpdateView(APIView):
    permission_classes = [IsClinician]

    def post(self, request, order_id):
        new_status = request.data.get("status")
        if not new_status:
            return Response(
                {"success": False, "message": "status is required", "data": None},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order = get_object_or_404(ClinicalOrder, id=order_id)
        current_status = order.status

        allowed = ORDER_STATUS_FLOW.get(current_status, [])
        if new_status not in allowed:
            return Response(
                {
                    "success": False,
                    "message": f"Invalid transition: {current_status} → {new_status}",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = new_status
        order.save(update_fields=["status"])

        audit(
            organization_id=order.organization_id,
            event_type="ORDER_STATUS_CHANGED",
            actor=request.user.username,
            order_id=str(order.id),
            meta={"from": current_status, "to": new_status},
        )

        return Response(
            {
                "success": True,
                "message": "Order status updated successfully",
                "data": {"order_id": str(order.id), "status": order.status},
            },
            status=status.HTTP_200_OK,
        )


# -------------------------------------------------
# 6.6 GET CLINICAL REPORT PDF (VALIDATED + FROZEN ONLY)
# -------------------------------------------------
class GetClinicalReportPDFView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, order_id):
        request_org_id = get_request_org_id(request)
        if not request_org_id:
            return Response(
                {"success": False, "message": "Missing X-ORG-ID header", "data": None},
                status=status.HTTP_403_FORBIDDEN,
            )

        order = get_object_or_404(ClinicalOrder, id=order_id)
        require_org_match(request_org_id, order.organization_id)

        report = get_object_or_404(ClinicalReport, order=order, is_frozen=True)

        # --- PHASE FINAL-1: BLOCK DELIVERY FOR CRITICAL FLAGS WITHOUT REVIEW ---
        safety = report.report_json.get("safety_flags", {})
        has_critical_flag = bool(safety.get("present"))

        if has_critical_flag and report.review_status != ClinicalReport.REVIEW_REVIEWED:
            return Response(
                {
                    "success": False,
                    "message": "clinician_review_required_for_critical_flags",
                    "data": None
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        # --- END PHASE FINAL-1 ---


        # ✅ STEP 3: block export until validated
        if report.validation_status != ClinicalReport.DATA_VALIDATED:
            return Response(
                {
                    "success": False,
                    "message": "Report data not validated",
                    "data": {"validation_status": report.validation_status},
                },
                status=status.HTTP_409_CONFLICT,
            )

        pdf_bytes = render_pdf_from_report_json_v1(report.report_json)

        # ✅ STEP 4: AUDIT LOG (Was Missing!)
        from backend.clinical.audit.models import ClinicalAuditEvent
        ClinicalAuditEvent.objects.create(
            organization_id=order.organization_id,
            event_type="PDF_EXPORTED",
            actor=str(request.user.id) if request.user.is_authenticated else "anonymous",
            order_id=order.id,
            report_id=report.id,
            meta={"file_name": f"report_{order_id}.pdf"},
        )

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="report_{order_id}.pdf"'
        return response
