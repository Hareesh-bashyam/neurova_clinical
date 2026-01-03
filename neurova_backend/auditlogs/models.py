from django.db import models
from django.contrib.auth.models import User
from core.models import Organization
from common.immutability import ImmutableModelMixin


class AuditLog(ImmutableModelMixin, models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    entity_type = models.CharField(max_length=50)
    entity_id = models.CharField(max_length=50)
    meta = models.JSONField(default=dict)
    ip = models.CharField(max_length=64, blank=True, default="")
    user_agent = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["organization", "created_at"]),
            models.Index(fields=["organization", "action"]),
        ]

    def __str__(self):
        return f"{self.action} {self.entity_type}:{self.entity_id}"
