from common.versioning import engine_version, report_schema_version


class VersionStampMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if hasattr(response, "data") and isinstance(response.data, dict):
            response.data.setdefault("engine_version", engine_version())
            response.data.setdefault("report_schema_version", report_schema_version())

        return response
