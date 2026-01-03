from django.db import models
from core.models import Organization
from sessions.models import Session
from common.immutability import ImmutableModelMixin


class RedFlagEvent(ImmutableModelMixin, models.Model):
    LEVELS = [
        ("AMBER", "AMBER"),
        ("RED", "RED"),
        ("CRITICAL", "CRITICAL"),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    flag_type = models.CharField(max_length=50)
    level = models.CharField(max_length=20, choices=LEVELS)
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["organization", "session"]),
            models.Index(fields=["organization", "level"]),
            models.Index(fields=["organization", "created_at"]),
        ]

    def __str__(self):
        return f"{self.flag_type} ({self.level})"


class FlagAcknowledgement(ImmutableModelMixin, models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    flag = models.ForeignKey(RedFlagEvent, on_delete=models.CASCADE)
    acknowledged_by_user_id = models.IntegerField()
    acknowledged_at = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        indexes = [
            models.Index(fields=["organization", "flag"]),
            models.Index(fields=["organization", "acknowledged_at"]),
        ]

    def __str__(self):
        return f"Ack {self.flag_id}"
