from apps.clinical_ops.audit.models import AuditEvent

def log_event(*, org_id: int, event_type: str, entity_type: str, entity_id: str,
              actor_user_id: str = None, actor_name: str = None, actor_role: str = None,
              details: dict = None):
    AuditEvent.objects.create(
        org_id=org_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=str(entity_id),
        actor_user_id=actor_user_id,
        actor_name=actor_name,
        actor_role=actor_role,
        details=details or {}
    )
