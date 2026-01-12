from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.utils import timezone
from django.db import transaction
from django.shortcuts import get_object_or_404

from common.permissions import IsClinician

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
from backend.clinical.reporting.pdf import render_pdf_from_report_json_v1

from reports.models import ClinicalReport
from django.http import HttpResponse



# -------------------------------------------------
# 6.1 CREATE ORDER
# -------------------------------------------------
class ClinicalOrderCreateView(APIView):
    permission_classes = [IsClinician]

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
                    {"error": f"Missing field: {field}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # validate battery
        get_battery_def(data["battery_code"])

        order = ClinicalOrder.objects.create(
            organization_id=data["organization_id"],
            patient_name=data["patient_name"],
            patient_age=data.get("patient_age"),
            patient_gender=data.get("patient_gender"),
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
                "order_id": str(order.id),
                "session_id": str(session.id),
                "battery_code": order.battery_code,
            },
            status=status.HTTP_201_CREATED,
        )


# -------------------------------------------------
# 6.2 START SESSION
# -------------------------------------------------
class StartSessionView(APIView):
    permission_classes = [IsClinician]

    def post(self, request, session_id):
        session = get_object_or_404(BatterySession, id=session_id)

        if session.status not in ["READY", "NOT_STARTED"]:
            return Response(
                {"error": "Session cannot be started"},
                status=status.HTTP_409_CONFLICT,
            )

        start_session(session)

        test_code = get_current_test_code(session)
        battery = get_battery_def(session.order.battery_code)

        return Response(
            {
                "session_id": str(session.id),
                "current_test_index": session.current_test_index,
                "test_code": test_code,
                "screening_label": battery["screening_label"],
            },
            status=200,
        )


# -------------------------------------------------
# 6.3 GET CURRENT TEST
# -------------------------------------------------
class GetCurrentTestView(APIView):
    permission_classes = [IsClinician]

    def get(self, request, session_id):
        session = get_object_or_404(BatterySession, id=session_id)

        if session.status != "IN_PROGRESS":
            return Response(
                {"error": "Session is not in progress"},
                status=status.HTTP_409_CONFLICT,
            )

        test_code = get_current_test_code(session)
        battery = get_battery_def(session.order.battery_code)

        return Response(
            {
                "session_id": str(session.id),
                "current_test_index": session.current_test_index,
                "test_code": test_code,
                "screening_label": battery["screening_label"],
            },
            status=200,
        )


# -------------------------------------------------
# 6.4 SUBMIT CURRENT TEST
# -------------------------------------------------
class SubmitCurrentTestView(APIView):
    permission_classes = [IsClinician]

    @transaction.atomic
    def post(self, request, session_id):
        session = get_object_or_404(BatterySession, id=session_id)

        if session.status != "IN_PROGRESS":
            return Response(
                {"error": "Session not in progress"},
                status=status.HTTP_409_CONFLICT,
            )

        raw_responses = request.data.get("raw_responses")
        if raw_responses is None:
            return Response(
                {"error": "raw_responses is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        test_run = open_current_test_run(session)

        test_run.raw_responses = raw_responses
        test_run.time_submitted = timezone.now()
        test_run.save(update_fields=["raw_responses", "time_submitted"])

        has_next = advance_to_next_test(session)

        audit(
            organization_id=session.organization_id,
            event_type="TEST_SUBMITTED",
            actor=request.user.username,
            session_id=str(session.id),
            meta={
                "test_code": test_run.test_code,
                "test_index": session.current_test_index,
            },
        )

        if not has_next:
            session.status = "COMPLETED"
            session.completed_at = timezone.now()
            session.save(update_fields=["status", "completed_at"])

            order = session.order
            order.status = "COMPLETED"
            order.save(update_fields=["status"])

            audit(
                organization_id=order.organization_id,
                event_type="SESSION_COMPLETED",
                actor=request.user.username,
                session_id=str(session.id),
                order_id=str(order.id),
            )

            return Response(
                {
                    "completed": True,
                    "order_id": str(order.id),
                    "report_ready": True,
                },
                status=200,
            )

        return Response(
            {
                "completed": False,
                "next_test_code": get_current_test_code(session),
                "next_test_index": session.current_test_index,
            },
            status=200,
        )


# -------------------------------------------------
# 6.5 GENERATE REPORT (NO RECOMPUTE)
# -------------------------------------------------
class GenerateReportView(APIView):
    permission_classes = [IsClinician]

    @transaction.atomic
    def post(self, request, order_id):
        order = get_object_or_404(ClinicalOrder, id=order_id)

        # 1️⃣ Order must be completed
        if order.status != "COMPLETED":
            return Response(
                {"error": "Order not completed"},
                status=status.HTTP_409_CONFLICT,
            )

        # 2️⃣ Session must exist (ClinicalOrder → sessions)
        session = order.sessions.first()
        if not session:
            return Response(
                {"error": "No session found for order"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 3️⃣ Session must be completed
        if session.status != "COMPLETED":
            return Response(
                {"error": "Session not completed"},
                status=status.HTTP_409_CONFLICT,
            )

        # 4️⃣ DO NOT RECOMPUTE (idempotent)
        existing = ClinicalReport.objects.filter(order=order).first()
        if existing:
            return Response(
                {"report_id": str(existing.id)},
                status=200,
            )

        # 5️⃣ Generate frozen report JSON
        report_json = generate_report_for_order_v1(order)

        report = ClinicalReport.objects.create(
            order=order,
            report_json=report_json,
            schema_version="v1",
            engine_version="v1.0.0",
            is_frozen=True,
        )

        return Response(
            {"report_id": str(report.id)},
            status=201,
        )


# -------------------------------------------------
# 6.6 GET PDF (READ ONLY, NO RECOMPUTE)
# -------------------------------------------------
class GetReportPDFView(APIView):
    permission_classes = [IsClinician]

    def get(self, request, order_id):
        report = get_object_or_404(
            ClinicalReport,
            order_id=order_id,
            is_frozen=True,
        )

        pdf_bytes = render_pdf_from_report_json_v1(report.report_json)

        response = Response(
            pdf_bytes,
            content_type="application/pdf",
        )
        response["Content-Disposition"] = (
            f'inline; filename="report_{order_id}.pdf"'
        )
        return response


# -------------------------------------------------
# ORDER STATUS UPDATE
# -------------------------------------------------
class ClinicalOrderStatusUpdateView(APIView):
    permission_classes = [IsClinician]

    def post(self, request, order_id):
        new_status = request.data.get("status")
        if not new_status:
            return Response({"error": "status is required"}, status=400)

        order = get_object_or_404(ClinicalOrder, id=order_id)
        current_status = order.status

        allowed = ORDER_STATUS_FLOW.get(current_status, [])
        if new_status not in allowed:
            return Response(
                {"error": f"Invalid transition: {current_status} → {new_status}"},
                status=400,
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
            {"order_id": str(order.id), "status": order.status},
            status=200,
        )

    
class GetClinicalReportPDFView(APIView):
    permission_classes = [IsClinician]

    def get(self, request, order_id):
        report = get_object_or_404(
            ClinicalReport,
            order_id=order_id,
            is_frozen=True,
        )

        pdf_bytes = render_pdf_from_report_json_v1(report.report_json)

        # ✅ CRITICAL: use HttpResponse, NOT DRF Response
        response = HttpResponse(
            pdf_bytes,
            content_type="application/pdf",
        )

        response["Content-Disposition"] = (
            f'inline; filename="report_{order_id}.pdf"'
        )

        return response