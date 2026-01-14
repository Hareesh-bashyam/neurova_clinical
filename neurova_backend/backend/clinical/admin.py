from django.contrib import admin
from django.http import HttpResponse

from backend.clinical.models import ClinicalOrder, BatterySession, TestRun
from reports.models import ClinicalReport
from backend.clinical.reporting.pdf_renderer_v1 import render_pdf_from_report_json_v1
from backend.clinical.signoff.services import apply_clinical_signoff
from backend.clinical.audit.services import audit
from django.contrib import messages

@admin.register(ClinicalOrder)
class ClinicalOrderAdmin(admin.ModelAdmin):
    list_display = ("id","organization_id","battery_code","status","created_at")
    list_filter = ("battery_code","status")
    search_fields = ("id","organization_id","battery_code")


@admin.register(BatterySession)
class BatterySessionAdmin(admin.ModelAdmin):
    list_display = ("id","organization_id","order","status","current_test_index","created_at")
    list_filter = ("status",)
    search_fields = ("id","organization_id","order__id")


@admin.register(TestRun)
class TestRunAdmin(admin.ModelAdmin):
    list_display = ("id","organization_id","session","test_code","test_order_index","time_submitted")
    list_filter = ("test_code",)
    search_fields = ("id","organization_id","session__id","test_code")


@admin.action(description="Download PDF (no recompute)")
def download_pdf(modeladmin, request, queryset):
    if queryset.count() != 1:
        modeladmin.message_user(
            request,
            "Select exactly one report.",
            level=messages.ERROR
        )
        return None

    rep = queryset.first()

    pdf_bytes = render_pdf_from_report_json_v1(rep.report_json)

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="report_{rep.order_id}.pdf"'
    )
    return response

@admin.action(description="Apply Signoff (fixed clinician fields)")
def apply_signoff_fixed(modeladmin, request, queryset):
    # V1 fixed fields (NO form). Update these constants only if AMR tells.
    CLINICIAN_NAME = "Dr. Clinical Reviewer"
    CLINICIAN_ROLE = "Psychiatrist"
    REG_NO = "REG-PLACEHOLDER"

    for rep in queryset:
        apply_clinical_signoff(
        rep,
        CLINICIAN_NAME,
        CLINICIAN_ROLE,
        REG_NO
    )

    modeladmin.message_user(request, "Signoff applied to selected reports.")


@admin.register(ClinicalReport)
class ClinicalReportAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "created_at")
    search_fields = ("id", "order__id")
    actions = [download_pdf, apply_signoff_fixed]
