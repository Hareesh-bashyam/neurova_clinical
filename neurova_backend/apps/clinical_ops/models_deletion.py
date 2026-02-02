from django.db import models
from django.utils import timezone
from apps.clinical_ops.models import AssessmentOrder
from core.models import Organization

class DeletionRequest(models.Model):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE)
    order = models.ForeignKey(AssessmentOrder, on_delete=models.CASCADE)

    requested_by = models.CharField(max_length=64)  # PATIENT / ADMIN
    reason = models.TextField()

    status = models.CharField(
        max_length=32,
        default="REQUESTED"  # REQUESTED / APPROVED / EXECUTED / REJECTED
    )

    requested_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["org", "status", "requested_at"]),
        ]
