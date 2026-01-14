from django.contrib import admin
from .models import ClinicalSignoff

@admin.register(ClinicalSignoff)
class ClinicalSignoffAdmin(admin.ModelAdmin):
    list_display = ("order", "status", "clinician_name", "signed_at")
    list_filter = ("status",)
    search_fields = ("order__id", "clinician_name")
