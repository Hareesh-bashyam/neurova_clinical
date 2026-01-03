from django.contrib import admin
from .models import Instrument, TestDefinition, Panel, PanelItem


@admin.register(Instrument)
class InstrumentAdmin(admin.ModelAdmin):
    list_display = ("id", "organization", "code", "version")
    list_filter = ("organization",)


@admin.register(TestDefinition)
class TestDefinitionAdmin(admin.ModelAdmin):
    list_display = ("id", "organization", "code", "version", "language", "is_active")
    list_filter = ("organization", "code", "language")


@admin.register(Panel)
class PanelAdmin(admin.ModelAdmin):
    list_display = ("id", "organization", "code", "is_active")
    list_filter = ("organization",)


@admin.register(PanelItem)
class PanelItemAdmin(admin.ModelAdmin):
    list_display = ("id", "panel", "test", "order_index")
