from django.db import models
from django.utils import timezone
from apps.clinical_ops.models import AssessmentOrder
from core.models import Organization

class AssessmentReport(models.Model):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE)
    order = models.OneToOneField(AssessmentOrder, on_delete=models.CASCADE, related_name="report")

    pdf_file = models.FileField(upload_to="clinical_reports/%Y/%m/%d/", null=True, blank=True)

    # sign-off fields (human or system)
    signoff_status = models.CharField(max_length=32, default="PENDING")  # PENDING/SIGNED/REJECTED
    signed_by_name = models.CharField(max_length=128, null=True, blank=True)
    signed_by_role = models.CharField(max_length=64, null=True, blank=True)  # Psychiatrist/Clinical Psychologist/System
    signed_at = models.DateTimeField(null=True, blank=True)

    generated_at = models.DateTimeField(default=timezone.now)
    generated_by_user_id = models.CharField(max_length=64, null=True, blank=True)
    signoff_reason = models.TextField(null=True, blank=True)  # why signed/rejected
    signoff_method = models.CharField(max_length=32, default="SYSTEM")  # SYSTEM/CLINICIAN

    class Meta:
        indexes = [
            models.Index(fields=["org", "generated_at"]),
            models.Index(fields=["org", "signoff_status"]),
        ]
