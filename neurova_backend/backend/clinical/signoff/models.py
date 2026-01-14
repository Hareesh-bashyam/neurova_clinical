import uuid
from django.db import models
from backend.clinical.models import ClinicalOrder

class ClinicalSignoff(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    order = models.OneToOneField(
        ClinicalOrder,
        on_delete=models.CASCADE,
        related_name="clinical_signoff"
    )

    status = models.CharField(
        max_length=20,
        default="PENDING"
    )  # PENDING | SIGNED

    clinician_name = models.CharField(max_length=200, blank=True)
    clinician_role = models.CharField(max_length=100, blank=True)
    registration_number = models.CharField(max_length=100, blank=True)

    signed_at = models.DateTimeField(null=True, blank=True)

