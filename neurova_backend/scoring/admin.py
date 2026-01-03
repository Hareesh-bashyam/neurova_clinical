from django.contrib import admin
from common.admin_readonly import ReadOnlyAdminMixin
from .models import Score


@admin.register(Score)
class ScoreAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("id", "session", "score", "severity", "created_at")
