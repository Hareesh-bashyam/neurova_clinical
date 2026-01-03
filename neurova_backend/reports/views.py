# reports/views.py

from rest_framework.views import APIView
from rest_framework.response import Response

from reports.models import Report, ReportSignature
from sessions.models import Session

from common.permissions import IsClinician,IsStaff
from common.versioning import engine_version, report_schema_version
from auditlogs.utils import log_event


class ReportCreateView(APIView):
    permission_classes = [IsStaff]

    def post(self, request, session_id):
        org = request.user.profile.organization

        # 1. Fetch session
        try:
            session = Session.objects.get(id=session_id, organization=org)
        except Session.DoesNotExist:
            return Response(
                {"error": "Session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 2. Ensure score exists
        try:
            score = Score.objects.get(session=session)
        except Score.DoesNotExist:
            return Response(
                {"error": "Session must be scored before report generation"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 3. Prevent duplicate report
        if Report.objects.filter(session=session).exists():
            return Response(
                {"error": "Report already exists for this session"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 4. Build report payload (SAFE FIELDS ONLY)
        report_payload = {
            "session_id": session.id,
            "score": score.score,
            "severity": score.severity,
            "generated_at": score.created_at.isoformat(),
        }

        # 5. Create report
        report = Report.objects.create(
            organization=org,
            session=session,
            report_json=report_payload,
            pdf_file="",  # placeholder (PDF pipeline later)
            status="READY",
            report_schema_version="v1",
            engine_version="v1.0.0",
        )

        # 6. Audit log
        log_event(
            request=request,
            org=org,
            action="REPORT_CREATED",
            entity_type="Report",
            entity_id=report.id,
        )

        return Response(
            {
                "report_id": report.id,
                "status": report.status,
            },
            status=status.HTTP_201_CREATED,
        )

class ReportSignView(APIView):
    permission_classes = [IsClinician]

    def post(self, request, report_id):
        report = Report.objects.get(
            id=report_id,
            organization=request.user.profile.organization
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

        return Response({"status": "signed"})

class ReportReleaseView(APIView):
    permission_classes = [IsClinician]

    def post(self, request, report_id):
        try:
            report = Report.objects.get(
                id=report_id,
                organization=request.user.profile.organization
            )
        except Report.DoesNotExist:
            return Response(
                {"error": "Report not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if report.status != "READY":
            return Response(
                {"error": "Only READY reports can be released"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if report.organization.signature_required:
            if not ReportSignature.objects.filter(report=report).exists():
                return Response(
                    {"error": "Signature required before release"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Controlled single mutation
        report.status = "RELEASED"
        report.save(update_fields=["status"])

        log_event(
            request,
            report.organization,
            "REPORT_RELEASED",
            "Report",
            report.id
        )

        return Response({"status": "released"})