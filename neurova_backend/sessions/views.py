# sessions/views.py
from rest_framework.views import APIView
from rest_framework.response import Response

from common.permissions import IsStaff
from auditlogs.utils import log_event
from .models import Session, SessionEvent, SessionConsent


class SessionEventCreateView(APIView):
    permission_classes = [IsStaff]

    def post(self, request, session_id):
        session = Session.objects.get(
            id=session_id,
            organization=request.user.profile.organization,
        )

        event = SessionEvent.objects.create(
            session=session,
            event_type=request.data["event_type"],
            source_screen=request.data.get("source_screen"),
            metadata=request.data.get("metadata", {}),
        )

        log_event(
            request,
            session.organization,
            "SESSION_EVENT_RECORDED",
            "SessionEvent",
            event.id,
        )

        return Response({"status": "event_recorded"})

class SessionConsentCreateView(APIView):
    permission_classes = [IsStaff]

    def post(self, request, session_id):
        session = Session.objects.get(
            id=session_id,
            organization=request.user.profile.organization,
        )

        consent = SessionConsent.objects.create(
            session=session,
            consent_given=request.data["consent_given"],
            source=request.data.get("source", "unknown"),
        )

        log_event(
            request,
            session.organization,
            "CONSENT_RECORDED",
            "SessionConsent",
            consent.id,
        )

        return Response({"status": "consent_recorded"})
