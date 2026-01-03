from django.contrib import admin
from .models import Patient

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "organization", "created_at")
    search_fields = ("name", "phone", "email")
    list_filter = ("organization",)
