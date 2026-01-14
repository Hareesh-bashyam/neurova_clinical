from django.db import models
import uuid

class OrgClinicalPolicy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization_id = models.UUIDField(unique=True)

    enabled_batteries = models.JSONField(default=list)
    signoff_required = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
