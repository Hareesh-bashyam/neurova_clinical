from django.contrib import admin
from .models import Order

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "organization", "patient", "status", "created_at")
    list_filter = ("organization", "status")
