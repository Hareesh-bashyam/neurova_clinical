import uuid
from django.db import models

class ClinicalAuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization_id = models.UUIDField(db_index=True)

    event_type = models.CharField(max_length=60)

    order_id = models.UUIDField(null=True, blank=True)
    session_id = models.UUIDField(null=True, blank=True)
    report_id = models.UUIDField(null=True, blank=True)

    actor = models.CharField(max_length=120, default="system")
    meta = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
