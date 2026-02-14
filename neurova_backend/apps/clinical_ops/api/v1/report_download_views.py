import hashlib

from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

from apps.clinical_ops.models import AssessmentOrder
from apps.clinical_ops.models_report import AssessmentReport
from apps.clinical_ops.audit.logger import log_event
from rest_framework.throttling import AnonRateThrottle


class StaffDownloadReport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        try:
            user = request.user
            org = user.profile.organization
            order_id = request.query_params.get("order_id")

            if not order_id:
                return Response(
                    {
                        "success": False,
                        "message": "Order id required",
                        "data": None
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Strict org isolation
            order = get_object_or_404(
                AssessmentOrder,
                id=order_id,
                org=org,
                deletion_status="ACTIVE",
            )

            # Role-based enforcement (example)
            if user.profile.role not in ["ADMIN", "PSYCHIATRIST", "STAFF"]:
                raise PermissionDenied("Insufficient permissions")

            # Only allow completed/delivered reports
            if order.status not in [
                AssessmentOrder.STATUS_AWAITING_REVIEW,
                AssessmentOrder.STATUS_COMPLETED,
                AssessmentOrder.STATUS_DELIVERED,
            ]:
                return Response(
                    {
                        "success": False,
                        "message": "Report not ready for download",
                        "data": None
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            report = get_object_or_404(
                AssessmentReport,
                order=order,
                org=org,
            )

            if not report.pdf_file:
                return Response(
                    {
                        "success": False,
                        "message": "PDF not generated",
                        "data": None
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Memory-safe integrity verification
            hasher = hashlib.sha256()
            with report.pdf_file.open("rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)

            current_hash = hasher.hexdigest()

            if report.pdf_sha256 and current_hash != report.pdf_sha256:
                log_event(
                    org=org,
                    event_type="REPORT_TAMPER_DETECTED",
                    entity_type="AssessmentOrder",
                    entity_id=order.id,
                    actor_user_id=str(user.id),
                    actor_role=user.profile.role,
                    request=request,
                    severity="CRITICAL"
                )

                return Response(
                    {
                        "success": False,
                        "message": "PDF integrity verification failed",
                        "data": None
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            # Audit successful download
            log_event(
                org=org,
                event_type="STAFF_REPORT_DOWNLOAD",
                entity_type="AssessmentOrder",
                entity_id=order.id,
                actor_user_id=str(user.id),
                actor_name=user.get_full_name(),
                actor_role=user.profile.role,
                request=request,
                severity="INFO"
            )

            response = FileResponse(
                report.pdf_file.open("rb"),
                content_type="application/pdf",
            )

            response["Content-Disposition"] = (
                f'attachment; filename="assessment_report_{order.id}.pdf"'
            )

            return response

        except PermissionDenied as e:
            return Response(
                {
                    "success": False,
                    "message": str(e),
                    "data": None
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        except Exception:
            return Response(
                {
                    "success": False,
                    "message": "Unable to download report at this time.",
                    "data": None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


MAX_ACCESS_ATTEMPTS = 5


class PublicDownloadReport(APIView):
    authentication_classes = []
    permission_classes = []
    throttle_classes = [AnonRateThrottle]

    def get(self, request, token):

        try:
            # 1. Validate & Rotate Secure Token
            order, new_token = validate_and_rotate_url_token(token, request)

            # 2. Delivery policy enforcement
            if order.delivery_mode != AssessmentOrder.DELIVERY_ALLOW_PATIENT_DOWNLOAD:
                raise PermissionDenied("Patient download not allowed")

            # 3. Optional expiry check (if you still keep link expiry logic)
            if order.public_link_expires_at and timezone.now() > order.public_link_expires_at:
                raise PermissionDenied("Link expired")

            # 4. Access code verification
            code = request.query_params.get("code")

            if not code:
                raise PermissionDenied("Access code required")

            # Lock protection
            if getattr(order, "report_access_locked", False):
                raise PermissionDenied("Access locked due to multiple failed attempts")

            if not verify_report_access_code(order, code):

                # Increment failure counter
                order.report_failed_attempts = getattr(order, "report_failed_attempts", 0) + 1

                if order.report_failed_attempts >= MAX_ACCESS_ATTEMPTS:
                    order.report_access_locked = True

                order.save(update_fields=["report_failed_attempts", "report_access_locked"])

                log_event(
                    org=order.org,
                    event_type="REPORT_DOWNLOAD_FAILED",
                    entity_type="AssessmentOrder",
                    entity_id=order.id,
                    actor_role="Patient",
                    details={"reason": "Invalid access code"},
                    request=request,
                    severity="SECURITY"
                )

                raise PermissionDenied("Invalid access code")

            # Reset failed attempts on success
            order.report_failed_attempts = 0
            order.save(update_fields=["report_failed_attempts"])

            # 5. Fetch report
            report = AssessmentReport.objects.filter(order=order).first()

            if not report or not report.pdf_file:
                return Response(
                    {
                        "success": False,
                        "message": "PDF not available",
                        "data": None
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # 6. Integrity Check (Memory-safe)
            hasher = hashlib.sha256()
            with report.pdf_file.open("rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)

            current_hash = hasher.hexdigest()

            if report.pdf_sha256 and current_hash != report.pdf_sha256:
                log_event(
                    org=order.org,
                    event_type="REPORT_TAMPER_DETECTED",
                    entity_type="AssessmentOrder",
                    entity_id=order.id,
                    actor_role="System",
                    request=request,
                    severity="CRITICAL"
                )

                return Response(
                    {
                        "success": False,
                        "message": "PDF integrity check failed",
                        "data": None
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            # 7. Audit successful download
            log_event(
                org=order.org,
                event_type="REPORT_DOWNLOAD_SUCCESS",
                entity_type="AssessmentOrder",
                entity_id=order.id,
                actor_role="Patient",
                request=request,
                severity="INFO"
            )

            # 8. Return file
            response = FileResponse(
                report.pdf_file.open("rb"),
                content_type="application/pdf",
            )

            response["Content-Disposition"] = (
                f'attachment; filename="assessment_report_{order.id}.pdf"'
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
                status=status.HTTP_403_FORBIDDEN,
            )

        except Exception:
            return Response(
                {
                    "success": False,
                    "message": "Unable to download report at this time.",
                    "data": None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )