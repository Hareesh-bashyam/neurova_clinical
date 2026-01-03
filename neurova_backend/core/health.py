from django.http import JsonResponse
from django.db import connection
from common.versioning import engine_version, report_schema_version


def healthz(request):
    return JsonResponse({"status": "ok"})


def readyz(request):
    try:
        with connection.cursor() as c:
            c.execute("SELECT 1")
        return JsonResponse({
            "status": "ready",
            "db": "ok",
            "engine_version": engine_version(),
            "report_schema_version": report_schema_version(),
        })
    except Exception:
        return JsonResponse({"status": "not_ready"}, status=503)
