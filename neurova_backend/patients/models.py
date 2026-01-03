from django.db import models
from core.models import Organization


class Patient(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    external_id = models.CharField(max_length=80, blank=True, default="")
    name = models.CharField(max_length=255)
    dob = models.DateField(null=True, blank=True)
    sex = models.CharField(max_length=20, blank=True, default="")
    phone = models.CharField(max_length=30, blank=True, default="")
    email = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        indexes = [
            models.Index(fields=["organization", "created_at"]),
            models.Index(fields=["organization", "name"]),
            models.Index(fields=["organization", "phone"]),
        ]
