from django.contrib import admin
from .models import ClinicalAuditEvent

@admin.register(ClinicalAuditEvent)
class ClinicalAuditEventAdmin(admin.ModelAdmin):
    list_display = ("organization_id", "event_type", "actor", "created_at")
    list_filter = ("event_type",)
    search_fields = ("organization_id", "event_type", "actor")
