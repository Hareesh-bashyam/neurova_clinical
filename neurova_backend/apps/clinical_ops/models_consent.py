from django.db import models
from django.utils import timezone
from apps.clinical_ops.models import AssessmentOrder, Org

class ConsentRecord(models.Model):
    org = models.ForeignKey(Org, on_delete=models.CASCADE)
    order = models.OneToOneField(AssessmentOrder, on_delete=models.CASCADE, related_name="consent")

    # versioning of consent text
    consent_version = models.CharField(max_length=32, default="V1")
    consent_language = models.CharField(max_length=16, default="en")  # en/hi/te...

    # who gave consent
    consent_given_by = models.CharField(max_length=32, default="SELF")  # SELF/GUARDIAN
    guardian_name = models.CharField(max_length=128, null=True, blank=True)

    # what was consented to
    allow_data_processing = models.BooleanField(default=True)
    allow_report_generation = models.BooleanField(default=True)
    allow_share_with_clinician = models.BooleanField(default=True)
    allow_patient_copy = models.BooleanField(default=False)

    # proof / metadata
    consent_text_snapshot = models.TextField()  # store exact text shown to patient
    consented_at = models.DateTimeField(default=timezone.now)
    ip_address = models.CharField(max_length=64, null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["org", "consent_version", "consented_at"]),
        ]
