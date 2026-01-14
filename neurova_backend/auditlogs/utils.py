from auditlogs.models import AuditLog


def log_event(request, org, action, entity_type, entity_id, meta=None):
    actor = None
    ip = ""
    user_agent = ""

    if request is not None:
        # actor
        if hasattr(request, "user") and getattr(request.user, "is_authenticated", False):
            actor = request.user

        # request metadata
        if hasattr(request, "META"):
            ip = request.META.get("REMOTE_ADDR", "")
            user_agent = request.META.get("HTTP_USER_AGENT", "")

    AuditLog.objects.create(
        organization=org,
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        meta=meta or {},
        ip=ip,
        user_agent=user_agent,
    )
