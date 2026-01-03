from django.contrib import admin
from common.admin_readonly import ReadOnlyAdminMixin
from .models import RedFlagEvent, FlagAcknowledgement


@admin.register(RedFlagEvent)
class RedFlagEventAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("id", "session", "level", "created_at")


@admin.register(FlagAcknowledgement)
class FlagAcknowledgementAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("id", "flag", "acknowledged_at")
