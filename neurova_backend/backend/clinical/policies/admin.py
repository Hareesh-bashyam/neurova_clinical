from django.contrib import admin
from .models import OrgClinicalPolicy

@admin.register(OrgClinicalPolicy)
class OrgClinicalPolicyAdmin(admin.ModelAdmin):
    list_display = ("organization_id", "signoff_required")
    search_fields = ("organization_id",)
