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
    severity="INFO",
    app_version=None  # Regulatory: track app version
):
    from django.conf import settings
    
    # Get app version from settings if not provided
    if app_version is None:
        app_version = getattr(settings, 'APP_VERSION', '1.0')

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
        severity=severity,
        app_version=app_version  # Regulatory: store app version
    )
