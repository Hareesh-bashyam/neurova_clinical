import logging
from rest_framework.views import exception_handler

logger = logging.getLogger("neurova.api")


def neurova_exception_handler(exc, context):
    request = context.get("request")
    response = exception_handler(exc, context)

    request_id = getattr(request, "request_id", None) if request else None
    path = getattr(request, "path", None) if request else None
    method = getattr(request, "method", None) if request else None

    # Log full exception server-side (JSON + stack trace)
    logger.exception(
        "api_exception",
        extra={
            "request_id": request_id,
            "path": path,
            "method": method,
        },
    )

    # Unhandled exception → safe 500
    if response is None:
        from rest_framework.response import Response
        from rest_framework import status

        return Response(
            {
                "success": False,
                "message": "Internal server error",
                "data": None,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Standardize error response shape
    if isinstance(response.data, dict):
        if "detail" in response.data:
            message = response.data["detail"]
        else:
            # Flatten validation errors to single message
            # e.g. {"field": ["Error"]} -> "field: Error"
            try:
                key, val = next(iter(response.data.items()))
                if isinstance(val, list):
                    val = val[0]
                message = f"{key}: {val}"
            except (StopIteration, TypeError):
                message = "Validation error"
    elif isinstance(response.data, list):
        # e.g. ["Error"] -> "Error"
        message = response.data[0] if response.data else "Error"
    else:
        message = str(response.data)

    current_data = {
        "success": False,
        "message": str(message),
        "data": None,
    }
    
    response.data = current_data
    return response
