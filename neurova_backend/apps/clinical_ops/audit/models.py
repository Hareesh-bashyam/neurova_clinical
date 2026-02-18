from django.db import models
from django.utils import timezone
from core.models import Organization

class AuditEvent(models.Model):

    org = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,  # Allow null for public/security events
        blank=True
    )

    event_type = models.CharField(max_length=64)
    entity_type = models.CharField(max_length=64, null=True, blank=True)
    entity_id = models.CharField(max_length=64, null=True, blank=True)

    actor_user_id = models.CharField(max_length=64, null=True, blank=True)
    actor_name = models.CharField(max_length=128, null=True, blank=True)
    actor_role = models.CharField(max_length=64, null=True, blank=True)

    # NEW SECURITY FIELDS
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=255, blank=True)

    severity = models.CharField(
        max_length=20,
        default="INFO"  # INFO / WARNING / ERROR / SECURITY
    )

    details = models.JSONField(default=dict)
    app_version = models.CharField(max_length=20, null=True, blank=True)  # Regulatory: track app version

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["org", "event_type", "created_at"]),
            models.Index(fields=["org", "entity_type", "entity_id"]),
            models.Index(fields=["event_type", "created_at"]),
        ]
