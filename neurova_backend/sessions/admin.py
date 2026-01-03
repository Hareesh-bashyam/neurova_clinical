from django.contrib import admin
from .models import ConsentRecord, Session, Response


@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "organization", "consent_version", "created_at")
    list_filter = ("organization", "consent_version")


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("id", "organization", "status", "created_at")
    list_filter = ("organization", "status")


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "test", "created_at")
