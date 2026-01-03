from .models import AuditLog


def log_event(request, org, action, entity_type, entity_id, meta=None):
    meta = meta or {}
    AuditLog.objects.create(
        organization=org,
        actor=request.user if request.user.is_authenticated else None,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        meta=meta,
        ip=request.META.get("REMOTE_ADDR", ""),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )
