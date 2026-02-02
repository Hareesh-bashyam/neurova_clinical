from django.db import models
from core.models import Organization
from patients.models import Patient
from orders.models import Order
from catalog.models import TestDefinition


class ConsentRecord(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="clinical_session_consents"
    )

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    consent_version = models.CharField(max_length=20)  # e.g. "v1"
    consent_text = models.TextField()
    language = models.CharField(max_length=20, default="en")
    captured_by = models.CharField(max_length=20, default="PATIENT")  # PATIENT / STAFF
    capture_mode = models.CharField(max_length=20, default="KIOSK")  # MOBILE / KIOSK
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["organization", "patient"]),
            models.Index(fields=["organization", "created_at"]),
        ]

    def __str__(self):
        return f"Consent {self.consent_version} for {self.patient_id}"


class Session(models.Model):
    STATUS = [
        ("CREATED", "CREATED"),
        ("STARTED", "STARTED"),
        ("SUBMITTED", "SUBMITTED"),
        ("SCORED", "SCORED"),
        ("REPORTED", "REPORTED"),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    order = models.OneToOneField(Order, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS, default="CREATED")
    started_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["organization", "created_at"]),
            models.Index(fields=["organization", "order"]),
        ]

    def __str__(self):
        return f"Session {self.id} ({self.status})"


class Response(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    test = models.ForeignKey(TestDefinition, on_delete=models.PROTECT)
    answers = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("organization", "session", "test")
        indexes = [
            models.Index(fields=["organization", "session"]),
            models.Index(fields=["organization", "test"]),
        ]

    def __str__(self):
        return f"Response {self.session_id} - {self.test.code}"

class SessionEvent(models.Model):
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name="events",
    )
    event_type = models.CharField(max_length=64)
    source_screen = models.CharField(max_length=128, blank=True, null=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

class SessionConsent(models.Model):
    session = models.OneToOneField(
        Session,
        on_delete=models.CASCADE,
        related_name="consent",
    )
    consent_given = models.BooleanField()
    source = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

