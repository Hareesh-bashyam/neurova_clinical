from django.db import models
from core.models import Organization
from patients.models import Patient
from catalog.models import Panel


class Order(models.Model):
    STATUS = [
        ("CREATED", "CREATED"),
        ("IN_PROGRESS", "IN_PROGRESS"),
        ("COMPLETED", "COMPLETED"),
        ("CANCELLED", "CANCELLED"),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT)
    panel = models.ForeignKey(Panel, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS, default="CREATED")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} ({self.status})"
