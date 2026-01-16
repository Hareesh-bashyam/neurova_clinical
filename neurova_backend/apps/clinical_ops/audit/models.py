from django.db import models
from django.utils import timezone
from apps.clinical_ops.models import Org

class AuditEvent(models.Model):
    org = models.ForeignKey(Org, on_delete=models.CASCADE)

    event_type = models.CharField(max_length=64)  # REPORT_SIGNED, REPORT_REJECTED, etc
    entity_type = models.CharField(max_length=64)  # AssessmentOrder/AssessmentReport
    entity_id = models.CharField(max_length=64)

    actor_user_id = models.CharField(max_length=64, null=True, blank=True)  # staff user id if any
    actor_name = models.CharField(max_length=128, null=True, blank=True)
    actor_role = models.CharField(max_length=64, null=True, blank=True)  # System / Psychiatrist / Staff

    details = models.JSONField(default=dict)  # store reason, flags, etc
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["org", "event_type", "created_at"]),
            models.Index(fields=["org", "entity_type", "entity_id"]),
        ]
