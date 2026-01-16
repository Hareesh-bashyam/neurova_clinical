from django.db import models
from django.utils import timezone
from apps.clinical_ops.models import AssessmentOrder, Org

class AssessmentResponse(models.Model):
    org = models.ForeignKey(Org, on_delete=models.CASCADE)
    order = models.OneToOneField(AssessmentOrder, on_delete=models.CASCADE, related_name="response")

    # raw answers from patient: list/dict stored as JSON
    answers_json = models.JSONField(default=dict)

    # metadata
    duration_seconds = models.IntegerField(default=0)
    submitted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["org", "submitted_at"]),
        ]

class AssessmentResult(models.Model):
    org = models.ForeignKey(Org, on_delete=models.CASCADE)
    order = models.OneToOneField(AssessmentOrder, on_delete=models.CASCADE, related_name="result")

    # calculated output stored as JSON
    result_json = models.JSONField(default=dict)

    # severity + flags summary (for queue display)
    primary_severity = models.CharField(max_length=64, blank=True, null=True)
    has_red_flags = models.BooleanField(default=False)

    computed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["org", "computed_at"]),
            models.Index(fields=["org", "has_red_flags"]),
        ]

