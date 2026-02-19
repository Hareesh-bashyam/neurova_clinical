from django.db import models
from django.utils import timezone
from apps.clinical_ops.services.retention_policy import compute_retention_date
from core.models import Organization    



class Org(models.Model):
    # If you already have Org/Tenant model, DO NOT use this.
    # Instead, delete this model and import your existing Org model everywhere.
    name = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


class Patient(models.Model):
    # If you already have Patient model, DO NOT duplicate.
    # Instead, delete this model and import your existing Patient model everywhere.
    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="patients")
    mrn = models.CharField(max_length=64, blank=True, null=True)  # UHID/MRN optional
    full_name = models.CharField(max_length=255)
    age = models.PositiveIntegerField()
    sex = models.CharField(max_length=16)  # keep simple: Male/Female/Other
    phone = models.CharField(max_length=32, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)



    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["org", "mrn"]),
            models.Index(fields=["org", "full_name"]),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.age}/{self.sex})"


class AssessmentOrder(models.Model):
    STATUS_CREATED = "CREATED"
    STATUS_IN_PROGRESS = "IN_PROGRESS"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_AWAITING_REVIEW = "AWAITING_REVIEW"
    STATUS_ACCEPTED = "ACCEPTED"
    STATUS_REJECTED = "REJECTED"
    STATUS_DELIVERED = "DELIVERED"
    STATUS_CANCELLED = "CANCELLED"

    STATUS_CHOICES = [
        (STATUS_CREATED, "Created"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_AWAITING_REVIEW, "Awaiting Review"),
        (STATUS_ACCEPTED, "Accepted"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    # Patient Acceptance Status
    ACCEPTANCE_PENDING = "PENDING"
    ACCEPTANCE_ACCEPTED = "ACCEPTED"
    ACCEPTANCE_REJECTED = "REJECTED"

    ACCEPTANCE_STATUS_CHOICES = [
        (ACCEPTANCE_PENDING, "Pending"),
        (ACCEPTANCE_ACCEPTED, "Accepted"),
        (ACCEPTANCE_REJECTED, "Rejected"),
    ]

    MODE_KIOSK = "KIOSK"
    MODE_QR_PHONE = "QR_PHONE"
    MODE_ASSISTED = "ASSISTED"

    MODE_CHOICES = [
        (MODE_KIOSK, "In-clinic kiosk/tablet"),
        (MODE_QR_PHONE, "Patient phone via QR/link"),
        (MODE_ASSISTED, "Assisted by staff"),
    ]

    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="orders")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="orders")

    battery_code = models.CharField(max_length=64)     # ex: MENTAL_HEALTH_CORE_V1
    battery_version = models.CharField(max_length=16, default="1.0")
    app_version = models.CharField(max_length=20, default="1.0")  # Regulatory: track app version


    encounter_type = models.CharField(max_length=16, default="OPD")  # OPD/IPD/WELLNESS
    referring_unit = models.CharField(max_length=128, blank=True, null=True)  # doctor/department

    administration_mode = models.CharField(max_length=16, choices=MODE_CHOICES, default=MODE_KIOSK)

    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_CREATED)

    created_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)

    created_by_user_id = models.CharField(max_length=64, blank=True, null=True)
    verified_by_staff = models.BooleanField(default=False)

    # links
    public_token = models.CharField(max_length=64, unique=False, null=True)
    public_link_expires_at = models.DateTimeField(blank=True, null=True)

    DELIVERY_HOSPITAL_ONLY = "HOSPITAL_ONLY"
    DELIVERY_ALLOW_PATIENT_DOWNLOAD = "ALLOW_PATIENT_DOWNLOAD"
    DELIVERY_EMAIL = "EMAIL"
    DELIVERY_SMS = "SMS"
    DELIVERY_PRINT = "PRINT"

    DELIVERY_CHOICES = [
        (DELIVERY_HOSPITAL_ONLY, "Hospital record only"),
        (DELIVERY_ALLOW_PATIENT_DOWNLOAD, "Allow patient download"),
        (DELIVERY_EMAIL, "Email"),
        (DELIVERY_SMS, "SMS"),
        (DELIVERY_PRINT, "Print"),
    ]

    delivery_mode = models.CharField(
            max_length=64,
            choices=DELIVERY_CHOICES,
            default=DELIVERY_HOSPITAL_ONLY
        )
    delivery_target = models.CharField(max_length=255, blank=True, null=True)  # email/phone if used
    report_access_code = models.CharField(max_length=8, blank=True, null=True)  # short code
    report_access_code_expires_at = models.DateTimeField(blank=True, null=True)
    data_retention_until = models.DateTimeField(null=True, blank=True)
    deletion_status = models.CharField(max_length=32,default="ACTIVE")  # ACTIVE / PENDING_DELETE / DELETED

    report_failed_attempts = models.PositiveSmallIntegerField(default=0)
    report_failed_attempts_locked_until = models.DateTimeField(null=True, blank=True)

    # Patient Acceptance Fields
    patient_acceptance_status = models.CharField(
        max_length=16,
        choices=ACCEPTANCE_STATUS_CHOICES,
        default=ACCEPTANCE_PENDING
    )
    patient_acceptance_timestamp = models.DateTimeField(blank=True, null=True)
    patient_acceptance_notes = models.TextField(blank=True, null=True)  # For rejection reasons
    patient_acceptance_remark = models.TextField(blank=True, null=True)
    

    class Meta:
        indexes = [
            models.Index(fields=["org", "status", "created_at"]),
            models.Index(fields=["org", "battery_code"]),
            models.Index(fields=["public_token"]),
        ]

    def save(self, *args, **kwargs):
        """
        Override save to apply data retention policy on first creation.
        """
        from apps.clinical_ops.services.retention_policy import compute_retention_date

        is_new = self.pk is None

        result = super().save(*args, **kwargs)

        # Apply retention only once, after first insert
        if is_new and self.data_retention_until is None:
            self.data_retention_until = compute_retention_date(self.created_at)
            super().save(update_fields=["data_retention_until"])

        return result

    def mark_completed(self):
        if self.status not in {
            self.STATUS_CREATED,
            self.STATUS_IN_PROGRESS,
        }:
            raise ValidationError(
                f"Cannot complete order from state {self.status}"
            )

        self.status = self.STATUS_COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at"])

    def mark_awaiting_review(self):
        if self.status != self.STATUS_COMPLETED:
            raise ValidationError(
                "Order must be completed before moving to review"
            )

        self.status = self.STATUS_AWAITING_REVIEW
        self.save(update_fields=["status"])


    def mark_started(self):
        """
        Ensure started_at is set exactly once.
        Safe to call multiple times.
        """
        if self.started_at:
            return  # idempotent

        self.started_at = timezone.now()
        self.save(update_fields=["status", "started_at"])



class ResponseQuality(models.Model):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE)
    order = models.OneToOneField(AssessmentOrder, on_delete=models.CASCADE, related_name="response_quality")

    duration_seconds = models.IntegerField(default=0)
    straight_lining_flag = models.BooleanField(default=False)
    too_fast_flag = models.BooleanField(default=False)
    inconsistency_flag = models.BooleanField(default=False)

    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

from .models_assessment import AssessmentResponse, AssessmentResult
from .models_report import AssessmentReport
from apps.clinical_ops.audit.models import AuditEvent
from apps.clinical_ops.models_consent import ConsentRecord
from apps.clinical_ops.models_deletion import DeletionRequest
from apps.clinical_ops.battery_assessment_model import Assessment, Battery, BatteryAssessment
from apps.clinical_ops.models_public_token import PublicAccessToken

