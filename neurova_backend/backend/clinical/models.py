import uuid
from django.db import models
from django.db.models import JSONField

class ClinicalOrder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(db_index=True, null=True, blank=True)

    patient_name = models.CharField(max_length=200)
    patient_age = models.IntegerField(null=True, blank=True)
    patient_gender = models.CharField(max_length=20, null=True, blank=True)

    # ✅ NEW FIELD
    phone_number = models.CharField(max_length=15, null=True, blank=True)

    encounter_type = models.CharField(max_length=20)  # OPD|IPD|DIAGNOSTIC
    administration_mode = models.CharField(max_length=20)  # IN_CLINIC|ASSISTED|QR

    battery_code = models.CharField(max_length=50)
    battery_version = models.CharField(max_length=10, default="1.0")

    status = models.CharField(max_length=30, default="CREATED")
    # CREATED|IN_PROGRESS|COMPLETED|CANCELLED

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.id} ({self.battery_code})"

class BatterySession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization_id = models.UUIDField(db_index=True)

    order = models.ForeignKey(
        ClinicalOrder,
        on_delete=models.CASCADE,
        related_name="sessions"
    )

    status = models.CharField(max_length=30, default="NOT_STARTED")
    # NOT_STARTED|IN_PROGRESS|COMPLETED

    current_test_index = models.IntegerField(default=0)

    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Session {self.id} ({self.status})"


class TestRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization_id = models.UUIDField(db_index=True)

    session = models.ForeignKey(
        BatterySession,
        on_delete=models.CASCADE,
        related_name="test_runs"
    )

    test_code = models.CharField(max_length=30)
    test_version = models.CharField(max_length=10, default="1.0")
    test_order_index = models.IntegerField()

    raw_responses = JSONField(default=list)  # must be list or dict (MDQ/ASRS)
    time_started = models.DateTimeField(null=True, blank=True)
    time_submitted = models.DateTimeField(null=True, blank=True)

    computed_score = models.IntegerField(null=True, blank=True)
    severity = models.CharField(max_length=50, null=True, blank=True)
    score_range = models.CharField(max_length=20, null=True, blank=True)
    reference = models.CharField(max_length=20, null=True, blank=True)

    red_flags = JSONField(default=list)  # ["SUICIDE_RISK"]

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.test_code} (#{self.test_order_index})"


class IdempotencyKey(models.Model):
    session = models.ForeignKey(
        "clinical.BatterySession",
        on_delete=models.CASCADE,
        related_name="idempotency_keys",
    )
    key = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["session", "key"],
                name="unique_idem_key_per_session",
            )
        ]

    def __str__(self):
        return f"IdempotencyKey(session={self.session_id}, key={self.key})"

