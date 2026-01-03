from django.contrib import admin
from common.admin_readonly import ReadOnlyAdminMixin
from .models import Report, ReportSignature


@admin.register(Report)
class ReportAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("id", "organization", "status", "created_at")


@admin.register(ReportSignature)
class ReportSignatureAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("id", "report", "signed_at")
