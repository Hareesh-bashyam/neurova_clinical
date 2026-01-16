from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from apps.clinical_ops.models import AssessmentOrder
from apps.clinical_ops.models_consent import ConsentRecord
from apps.clinical_ops.services.consent_text import get_consent_text
from apps.clinical_ops.audit.logger import log_event

class PublicGetConsent(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, token):
        order = get_object_or_404(AssessmentOrder, public_token=token)
        text = get_consent_text(version="V1", lang="en")
        return Response({
            "consent_version": "V1",
            "consent_language": "en",
            "consent_text": text
        }, status=status.HTTP_200_OK)

class PublicSubmitConsent(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, token):
        order = get_object_or_404(AssessmentOrder, public_token=token)

        consent_version = request.data.get("consent_version") or "V1"
        consent_language = request.data.get("consent_language") or "en"
        consent_given_by = request.data.get("consent_given_by") or "SELF"
        guardian_name = request.data.get("guardian_name")

        allow_patient_copy = bool(request.data.get("allow_patient_copy", False))

        text = get_consent_text(consent_version, consent_language)

        cr, _ = ConsentRecord.objects.update_or_create(
            org_id=order.org_id,
            order=order,
            defaults={
                "consent_version": consent_version,
                "consent_language": consent_language,
                "consent_given_by": consent_given_by,
                "guardian_name": guardian_name if consent_given_by == "GUARDIAN" else None,
                "allow_data_processing": True,
                "allow_report_generation": True,
                "allow_share_with_clinician": True,
                "allow_patient_copy": allow_patient_copy,
                "consent_text_snapshot": text,
                "ip_address": request.META.get("REMOTE_ADDR"),
                "user_agent": request.META.get("HTTP_USER_AGENT"),
                "consented_at": timezone.now(),
            }
        )

        # map to delivery policy if patient copy allowed
        if allow_patient_copy:
            order.delivery_mode = AssessmentOrder.DELIVERY_ALLOW_PATIENT_DOWNLOAD
            order.save(update_fields=["delivery_mode"])

        log_event(
            org_id=order.org_id,
            event_type="CONSENT_CAPTURED",
            entity_type="AssessmentOrder",
            entity_id=order.id,
            actor_role="Patient",
            details={
                "consent_version": consent_version,
                "consent_language": consent_language,
                "consent_given_by": consent_given_by,
                "allow_patient_copy": allow_patient_copy
            }
        )

        return Response({"ok": True,"consent_version": consent_version,
                        "consent_language": consent_language,
                        "consent_given_by": consent_given_by,
                        "allow_patient_copy": allow_patient_copy,
                        "consent_id": cr.id}, 
                        status=status.HTTP_200_OK)

