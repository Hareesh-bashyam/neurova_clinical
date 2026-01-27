from django.http import HttpResponse
from django.core.exceptions import ValidationError
from django.db import transaction
from datetime import date

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from reports.models import Report, ReportSignature
from sessions.models import Session
from scoring.models import Score

from common.permissions import IsClinician, IsStaff
from auditlogs.utils import log_event

from backend.clinical.reporting.pdf_renderer_v1 import (
    render_pdf_from_report_json_v1
)
from backend.clinical.reporting.report_schema_v1 import build_report_json_v1
from backend.clinical.reporting import normalizers_v1
from django.utils import timezone
from django.shortcuts import get_object_or_404
from reports.models import ClinicalReport
from rest_framework.permissions import IsAuthenticated


# ===============================================================
# CREATE REPORT (STAFF) — CANONICAL & IMMUTABLE SAFE
# ===============================================================

class ReportCreateView(APIView):
    permission_classes = [IsStaff]

    @transaction.atomic
    def post(self, request, session_id):
        org_obj = request.user.profile.organization

        # 1️⃣ Fetch session
        try:
            session = Session.objects.select_related(
                "order__patient",
                "order__panel",
            ).get(id=session_id, organization=org_obj)
        except Session.DoesNotExist:
            return Response({"error": "Session not found"}, status=404)

        # 2️⃣ Ensure session is scored
        try:
            score = Score.objects.get(session=session)
        except Score.DoesNotExist:
            return Response(
                {"error": "Session must be scored before report generation"},
                status=400,
            )

        # 3️⃣ Prevent duplicate report
        if Report.objects.filter(session=session).exists():
            return Response(
                {"error": "Report already exists for this session"},
                status=400,
            )

        # 4️⃣ Create report with SAFE placeholder
        report = Report.objects.create(
            organization=org_obj,
            session=session,
            report_json={"_state": "BUILDING"},
            status="READY",
        )

        # 5️⃣ Build canonical JSON (V1 — FROZEN)
        report_json = build_report_json_v1(
            report_id=str(report.id),
            org=normalizers_v1.normalize_organization(org_obj),
            patient=normalizers_v1.normalize_patient(session.order.patient),
            encounter=normalizers_v1.normalize_encounter(session),
            battery={
                "code": session.order.panel.code,
                "version": "1.0",
            },
            test_results=normalizers_v1.normalize_test_results(score),
            flags=[],
            signoff=normalizers_v1.normalize_signoff(org_obj),
        )

        # 6️⃣ Hard validation
        if not report_json or "organization" not in report_json:
            raise ValidationError(
                "Canonical report_json invalid — build_report_json_v1 failed"
            )
        
        # 7️⃣ Immutable-safe update
        Report.objects.filter(pk=report.pk).update(report_json=report_json)

        # 8️⃣ Audit log
        log_event(
            request=request,
            org=org_obj,
            action="REPORT_CREATED",
            entity_type="Report",
            entity_id=report.id,
        )

        return Response(
            {"report_id": report.id, "status": report.status},
            status=status.HTTP_201_CREATED,
        )


# ===============================================================
# SIGN REPORT (CLINICIAN)
# ===============================================================

class ReportSignView(APIView):
    permission_classes = [IsClinician]

    def post(self, request, report_id):
        try:
            report = Report.objects.get(
                id=report_id,
                organization=request.user.profile.organization,
            )
        except Report.DoesNotExist:
            return Response({"error": "Report not found"}, status=404)

        if report.status != "READY":
            return Response(
                {"error": "Only READY reports can be signed"},
                status=400,
            )

        signature = ReportSignature.objects.create(
            organization=report.organization,
            report=report,
            signer_name=request.data["signer_name"],
            signer_reg_no=request.data["signer_reg_no"],
            signer_role=request.data["signer_role"],
            signature_meta=request.data.get("meta", {}),
        )

        log_event(
            request,
            report.organization,
            "REPORT_SIGNED",
            "ReportSignature",
            signature.id,
        )

        return Response({"status": "signed"}, status=200)


# ===============================================================
# RELEASE REPORT (CLINICIAN)
# ===============================================================

class ReportReleaseView(APIView):
    permission_classes = [IsClinician]

    def post(self, request, report_id):
        try:
            report = Report.objects.get(
                id=report_id,
                organization=request.user.profile.organization,
            )
        except Report.DoesNotExist:
            return Response({"error": "Report not found"}, status=404)

        # 🔒 Signature gate (policy check, no mutation)
        if report.organization.signature_required:
            if not ReportSignature.objects.filter(report=report).exists():
                return Response(
                    {"error": "Signature required before release"},
                    status=400,
                )

        # 🧾 AUDIT ONLY — NO REPORT MUTATION
        log_event(
            request,
            report.organization,
            "REPORT_RELEASED",
            "Report",
            report.id,
        )

        return Response(
            {
                "status": "released",
                "report_id": report.id,
            },
            status=200,
        )


# ===============================================================
# VIEW / DOWNLOAD PDF — CANONICAL JSON ONLY (V1)
# ===============================================================

class ReportPDFView(APIView):
    permission_classes = [IsClinician]

    def get(self, request, report_id):
        try:
            report = Report.objects.get(
                id=report_id,
                organization=request.user.profile.organization,
            )
        except Report.DoesNotExist:
            return Response({"error": "Report not found"}, status=404)

        if not report.report_json:
            return Response(
                {"detail": "Report JSON not available. Generate report first."},
                status=status.HTTP_409_CONFLICT,
            )

        pdf_bytes = render_pdf_from_report_json_v1(report.report_json)

        return HttpResponse(pdf_bytes, content_type="application/pdf")


# -------------------------------------------------
# MARK REPORT AS REVIEWED
# -------------------------------------------------
class MarkReportReviewedView(APIView):
    """
    Marks a ClinicalReport as reviewed by a clinician/staff.
    No UI dependency. No PDF generation. No recomputation.
    """

    permission_classes = [IsClinician]  # keep same auth pattern as other report endpoints

    def post(self, request, report_id):
        report = get_object_or_404(
            ClinicalReport,
            id=report_id,
        )

        # ---- REVIEW METADATA ----
        report.review_status = ClinicalReport.REVIEW_REVIEWED
        report.reviewed_by_user_id = (
            str(getattr(request.user, "id", None))
            if request.user and request.user.is_authenticated
            else None
        )

        report.reviewed_by_name = (
            request.user.get_full_name()
            if request.user and request.user.is_authenticated and hasattr(request.user, "get_full_name")
            else getattr(request.user, "username", None)
        )

        report.reviewed_by_role = "Clinician"
        report.reviewed_at = timezone.now()

        # ---- VALIDATION COUPLING (PHASE FINAL–1 RULE) ----
        if report.validation_status == ClinicalReport.VALIDATION_PENDING:
            report.validation_status = ClinicalReport.DATA_VALIDATED

        report.save(update_fields=[
            "review_status",
            "reviewed_by_user_id",
            "reviewed_by_name",
            "reviewed_by_role",
            "reviewed_at",
            "validation_status",
        ])

        return Response(
            {
                "ok": True,
                "review_status": report.review_status,
                "validation_status": report.validation_status,
            },
            status=status.HTTP_200_OK,
        )

class CreateReportCorrectionView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, report_id):
        old = get_object_or_404(
            ClinicalReport,
            id=report_id,
            is_active=True,
        )

        reason = request.data.get("correction_reason", "").strip()

        # 1) Deactivate old report
        old.is_active = False
        old.save(update_fields=["is_active"])

        # 2) Create corrected report (same order, same data)
        new = ClinicalReport.objects.create(
            order=old.order,
            report_json=old.report_json,
            validation_status=ClinicalReport.DATA_VALIDATED,
            review_status=ClinicalReport.REVIEW_DRAFT,
            supersedes_report=old,
            is_active=True,
            correction_reason=reason or None,
        )

        return Response(
            {
                "ok": True,
                "new_report_id": new.id,
            },
            status=status.HTTP_201_CREATED,
        )