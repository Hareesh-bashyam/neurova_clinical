import os
from django.db import models
from django.core.exceptions import ValidationError
from core.models import Organization
from sessions.models import Session
from common.immutability import ImmutableModelMixin
from .storage_paths import report_upload_path


class Report(ImmutableModelMixin, models.Model):
    STATUS = [
        ("DRAFT", "DRAFT"),
        ("READY", "READY"),
        ("RELEASED", "RELEASED"),
    ]

    RELEASE = [
        ("CLINICIAN_ONLY", "CLINICIAN_ONLY"),
        ("PATIENT_AND_CLINICIAN", "PATIENT_AND_CLINICIAN"),
    ]
    

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    session = models.OneToOneField(Session, on_delete=models.PROTECT)

    report_json = models.JSONField()

    pdf_file = models.FileField(
        upload_to=report_upload_path,
        null=True,
        blank=True,
        default=None,
    )

    status = models.CharField(max_length=20, choices=STATUS, default="READY")
    release_policy = models.CharField(
        max_length=30,
        choices=RELEASE,
        default="CLINICIAN_ONLY"
    )

    report_schema_version = models.CharField(max_length=20)
    engine_version = models.CharField(max_length=20)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["organization", "created_at"]),
        ]

    def __str__(self):
        return f"Report {self.id}"

    # 🔐 STATE TRANSITIONS (IMMUTABLE SAFE)

    def release(self):
        if self.status != "READY":
            raise ValidationError("Only READY reports can be released")
        Report.objects.filter(pk=self.pk).update(status="RELEASED")

    def mark_ready(self):
        if self.status != "DRAFT":
            raise ValidationError("Only DRAFT reports can be marked READY")
        Report.objects.filter(pk=self.pk).update(status="READY")

    # 🔒 FILEFIELD HARD SAFETY

    def clean(self):
        if self.pdf_file:
            value = str(self.pdf_file.name)

            if "/" not in value:
                raise ValidationError({"pdf_file": "Invalid file path"})

            if not value.lower().endswith(".pdf"):
                raise ValidationError({"pdf_file": "pdf_file must be a PDF"})

    @property
    def safe_pdf_path(self):
        try:
            if not self.pdf_file:
                return None
            path = self.pdf_file.path
            return path if os.path.exists(path) else None
        except Exception:
            return None


class ReportSignature(ImmutableModelMixin, models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    report = models.ForeignKey(Report, on_delete=models.CASCADE)

    signer_name = models.CharField(max_length=255)
    signer_reg_no = models.CharField(max_length=100)
    signer_role = models.CharField(max_length=100)

    signed_at = models.DateTimeField(auto_now_add=True)
    signature_meta = models.JSONField(default=dict)

    class Meta:
        indexes = [
            models.Index(fields=["organization", "signed_at"]),
            models.Index(fields=["organization", "report"]),
        ]

    def __str__(self):
        return f"Signature for Report {self.report_id}"

class ClinicalReport(models.Model):
    order = models.OneToOneField(
        "clinical.ClinicalOrder",
        on_delete=models.CASCADE,
        related_name="clinicalreport",
    )

    schema_version = models.CharField(max_length=10)
    engine_version = models.CharField(max_length=10)

    report_json = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    is_frozen = models.BooleanField(default=True)

    class Meta:
        db_table = "reports_clinicalreport"
