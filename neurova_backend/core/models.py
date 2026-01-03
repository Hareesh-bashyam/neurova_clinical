from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class Organization(models.Model):
    ORG_TYPES = [("HOSPITAL","HOSPITAL"),("DIAGNOSTIC","DIAGNOSTIC")]
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)  # used in S3 path
    org_type = models.CharField(max_length=20, choices=ORG_TYPES)
    signature_required = models.BooleanField(default=False)
    default_release_policy = models.CharField(
        max_length=30,
        choices=[("CLINICIAN_ONLY","CLINICIAN_ONLY"),("PATIENT_AND_CLINICIAN","PATIENT_AND_CLINICIAN")],
        default="CLINICIAN_ONLY",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    ROLES = [("ORG_ADMIN","ORG_ADMIN"),("CLINICIAN","CLINICIAN"),("STAFF","STAFF"),("AUDITOR","AUDITOR")]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLES)

    def __str__(self):
        return f"{self.user.username} ({self.role})"

