from .models import ClinicalAuditEvent

def audit(
    organization_id,
    event_type,
    actor="system",
    order_id=None,
    session_id=None,
    report_id=None,
    meta=None
):
    ClinicalAuditEvent.objects.create(
        organization_id=organization_id,
        event_type=event_type,
        actor=actor or "system",
        order_id=order_id,
        session_id=session_id,
        report_id=report_id,
        meta=meta or {}
    )
