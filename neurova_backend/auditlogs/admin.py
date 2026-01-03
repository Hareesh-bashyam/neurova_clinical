from django.contrib import admin
from common.admin_readonly import ReadOnlyAdminMixin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("id", "organization", "action", "entity_type", "created_at")
