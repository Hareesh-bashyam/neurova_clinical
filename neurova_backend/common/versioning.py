from django.conf import settings

def engine_version():
    return getattr(settings, "ENGINE_VERSION", "v1.0.0")

def report_schema_version():
    return getattr(settings, "REPORT_SCHEMA_VERSION", "v1")

