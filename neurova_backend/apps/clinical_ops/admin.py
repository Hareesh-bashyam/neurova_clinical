from django.contrib import admin

from apps.clinical_ops.models import (
    Org,
    Patient,
    AssessmentOrder,
    ResponseQuality,
)

from apps.clinical_ops.models_assessment import (
    AssessmentResponse,
    AssessmentResult,
)

from apps.clinical_ops.models_report import AssessmentReport
from apps.clinical_ops.models_consent import ConsentRecord
from apps.clinical_ops.models_deletion import DeletionRequest
from apps.clinical_ops.battery_assessment_model import Assessment, Battery, BatteryAssessment



# =========================
# ORG
# =========================
@admin.register(Org)
class OrgAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_active", "created_at")
    search_fields = ("name",)
    list_filter = ("is_active",)


# =========================
# PATIENT
# =========================
@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "age", "sex", "phone", "org")
    search_fields = ("full_name", "phone", "email", "mrn")
    list_filter = ("org", "sex")
    autocomplete_fields = ("org",)


# =========================
# ASSESSMENT ORDER
# =========================
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


# =========================
# RESPONSE QUALITY
# =========================
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


# =========================
# ASSESSMENT RESPONSE (RAW ANSWERS)
# =========================
@admin.register(AssessmentResponse)
class AssessmentResponseAdmin(admin.ModelAdmin):
    list_display = ("id", "org", "order", "submitted_at", "duration_seconds")
    search_fields = ("order__public_token",)
    list_filter = ("org", "submitted_at")
    readonly_fields = ("submitted_at",)
    autocomplete_fields = ("org", "order")


# =========================
# ASSESSMENT RESULT (SCORED)
# =========================
@admin.register(AssessmentResult)
class AssessmentResultAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "org",
        "order",
        "primary_severity",
        "has_red_flags",
        "computed_at",
    )
    list_filter = ("org", "has_red_flags")
    readonly_fields = ("computed_at",)
    autocomplete_fields = ("org", "order")


# =========================
# ASSESSMENT REPORT (PDF)
# =========================
@admin.register(AssessmentReport)
class AssessmentReportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "org",
        "order",
        "signoff_status",
        "signed_by_role",
        "generated_at",
    )
    list_filter = ("org", "signoff_status")
    readonly_fields = ("generated_at",)
    autocomplete_fields = ("org", "order")


# =========================
# CONSENT RECORD
# =========================
@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "org",
        "order",
        "consent_version",
        "consent_language",
        "consented_at",
    )
    list_filter = ("org", "consent_language")
    readonly_fields = ("consented_at",)
    autocomplete_fields = ("org", "order")


# =========================
# DATA DELETION REQUEST
# =========================
@admin.register(DeletionRequest)
class DeletionRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "org",
        "order",
        "status",
        "requested_by",
        "requested_at",
    )
    list_filter = ("org", "status")
    readonly_fields = ("requested_at", "processed_at")
    autocomplete_fields = ("org", "order")


class BatteryAssessmentInline(admin.TabularInline):
    model = BatteryAssessment
    extra = 1
    autocomplete_fields = ("assessment",)
    fields = ("assessment", "display_order")


@admin.register(Battery)
class BatteryAdmin(admin.ModelAdmin):
    list_display = (
        "battery_code",
        "name",
        "version",
        "signoff_required",
        "is_active",
    )
    search_fields = ("battery_code", "name")

    inlines = [BatteryAssessmentInline]

    fieldsets = (
        ("Basic Info", {
            "fields": (
                "battery_code",
                "name",
                "version",
                "screening_label",
                "signoff_required",
                "is_active",
            )
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ("battery_code",)
        return ()


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ("test_code", "title", "version", "is_active")
    search_fields = ("test_code", "title")

    fieldsets = (
        ("Basic Info", {
            "fields": (
                "test_code",
                "title",
                "version",
                "description",
                "is_active",
            )
        }),
        ("Questions JSON", {
            "fields": ("questions_json",),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ("test_code",)
        return ()