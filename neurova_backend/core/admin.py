from django.contrib import admin
from .models import Organization, UserProfile
# Register your models here.


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "code", "org_type", "signature_required", "created_at")
    search_fields = ("name", "code")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "organization", "role")
    list_filter = ("role", "organization")
