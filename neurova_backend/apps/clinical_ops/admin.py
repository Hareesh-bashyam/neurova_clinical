from django.contrib import admin

from .models import (
    Org,
    Patient,
    AssessmentOrder,
    ResponseQuality,
)


@admin.register(Org)
class OrgAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_active", "created_at")
    search_fields = ("name",)
    list_filter = ("is_active",)


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "age", "sex", "phone", "org")
    search_fields = ("full_name", "phone", "email", "mrn")
    list_filter = ("org", "sex")
    autocomplete_fields = ("org",)


@admin.register(AssessmentOrder)
class AssessmentOrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "org",
        "patient",
        "battery_code",
        "status",
        "administration_mode",
        "created_at",
    )
    search_fields = (
        "battery_code",
        "public_token",
        "patient__full_name",
    )
    list_filter = (
        "status",
        "battery_code",
        "administration_mode",
        "org",
    )
    readonly_fields = (
        "public_token",
        "created_at",
        "started_at",
        "completed_at",
        "delivered_at",
        "data_retention_until",
    )
    autocomplete_fields = ("org", "patient")


@admin.register(ResponseQuality)
class ResponseQualityAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "org",
        "order",
        "duration_seconds",
        "straight_lining_flag",
        "too_fast_flag",
        "inconsistency_flag",
        "created_at",
    )
    list_filter = (
        "straight_lining_flag",
        "too_fast_flag",
        "inconsistency_flag",
        "org",
    )
