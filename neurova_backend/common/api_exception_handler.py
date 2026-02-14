import logging
from rest_framework.views import exception_handler
from apps.clinical_ops.audit.models import AuditEvent

logger = logging.getLogger("neurova.api")


def neurova_exception_handler(exc, context):
    request = context.get("request")
    response = exception_handler(exc, context)

    request_id = getattr(request, "request_id", None) if request else None
    path = getattr(request, "path", None) if request else None
    method = getattr(request, "method", None) if request else None

    # Always log full exception to logger (stack trace safe internally)
    logger.exception(
        "api_exception",
        extra={
            "request_id": request_id,
            "path": path,
            "method": method,
        },
    )

    status_code = response.status_code if response else 500

    # Log SECURITY (401/403) and SYSTEM (500) errors to DB
    if status_code in [401, 403, 500]:
        try:
            AuditEvent.objects.create(
                org=None,
                event_type="SECURITY_VIOLATION" if status_code in [401, 403] else "SYSTEM_ERROR",
                entity_type=None,
                entity_id=None,
                actor_user_id=None,
                actor_name=None,
                actor_role="System",
                details={
                    "error_type": exc.__class__.__name__,
                    "error_code": getattr(exc, "default_code", "error"),
                },
                ip_address=request.META.get("REMOTE_ADDR") if request else None,
                user_agent=request.META.get("HTTP_USER_AGENT") if request else "",
                request_path=path or "",
                severity="SECURITY" if status_code in [401, 403] else "ERROR",
            )
        except Exception:
            # Never break API because of logging failure
            pass

    # 🔴 Unhandled exception → safe 500
    if response is None:
        from rest_framework.response import Response
        from rest_framework import status

        return Response(
            {
                "success": False,
                "error_code": "internal_error",
                "message": "Internal server error",
                "data": None,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # 🔹 Standardize error response shape (your existing logic preserved)

    if isinstance(response.data, dict):
        if "detail" in response.data:
            message = response.data["detail"]
        else:
            try:
                key, val = next(iter(response.data.items()))
                if isinstance(val, list):
                    val = val[0]
                message = f"{key}: {val}"
            except (StopIteration, TypeError):
                message = "Validation error"

    elif isinstance(response.data, list):
        message = response.data[0] if response.data else "Error"
    else:
        message = str(response.data)

    response.data = {
        "success": False,
        "error_code": getattr(exc, "default_code", "error"),
        "message": str(message),
        "data": None,
    }

    return response
