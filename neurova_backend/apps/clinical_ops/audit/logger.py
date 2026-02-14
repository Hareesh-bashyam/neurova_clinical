from apps.clinical_ops.audit.models import AuditEvent

def log_event(
    *,
    org=None,
    event_type,
    entity_type=None,
    entity_id=None,
    actor_user_id=None,
    actor_name=None,
    actor_role=None,
    details=None,
    request=None,
    severity="INFO"
):

    AuditEvent.objects.create(
        org=org,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else None,
        actor_user_id=actor_user_id,
        actor_name=actor_name,
        actor_role=actor_role,
        details=details or {},
        ip_address=request.META.get("REMOTE_ADDR") if request else None,
        user_agent=request.META.get("HTTP_USER_AGENT") if request else "",
        request_path=request.path if request else "",
        severity=severity
    )
