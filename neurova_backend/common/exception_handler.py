from rest_framework.views import exception_handler
from rest_framework import status
from apps.clinical_ops.audit.models import AuditEvent


def custom_exception_handler(exc, context):
    """
    Global exception handler:
    - Standardizes API error response
    - Logs SECURITY and SYSTEM errors to DB
    - HIPAA-safe (no raw data, no stack traces)
    """

    response = exception_handler(exc, context)
    request = context.get("request")

    if response is None:
        # Unhandled exception (500)
        _log_exception(
            request=request,
            event_type="SYSTEM_ERROR",
            severity="ERROR",
            details={"error_type": exc.__class__.__name__}
        )

        return _standard_response(
            message="Internal server error.",
            error_code="internal_error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # Handle known DRF exceptions
    status_code = response.status_code

    if status_code in [401, 403]:
        _log_exception(
            request=request,
            event_type="SECURITY_VIOLATION",
            severity="SECURITY",
            details={
                "error_code": getattr(exc, "default_code", "auth_error")
            }
        )

    elif status_code >= 500:
        _log_exception(
            request=request,
            event_type="SYSTEM_ERROR",
            severity="ERROR",
            details={
                "error_type": exc.__class__.__name__
            }
        )

    return _standard_response(
        message=response.data.get("detail", "Request failed."),
        error_code=getattr(exc, "default_code", "error"),
        status_code=status_code
    )


def _log_exception(request, event_type, severity, details):
    try:
        AuditEvent.objects.create(
            org=None,  # Public / system level
            event_type=event_type,
            entity_type=None,
            entity_id=None,
            actor_user_id=None,
            actor_name=None,
            actor_role="System",
            details=details,
            ip_address=request.META.get("REMOTE_ADDR") if request else None,
            user_agent=request.META.get("HTTP_USER_AGENT") if request else "",
            request_path=request.path if request else "",
            severity=severity
        )
    except Exception:
        # Never break API due to logging failure
        pass


def _standard_response(message, error_code, status_code):
    from rest_framework.response import Response
    return Response(
        {
            "success": False,
            "error_code": error_code,
            "message": message,
            "data": None
        },
        status=status_code
    )
