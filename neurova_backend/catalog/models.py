from django.db import models
from core.models import Organization


class Instrument(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    version = models.CharField(max_length=20)
    owner = models.CharField(max_length=255, blank=True, default="")
    license_type = models.CharField(max_length=50, blank=True, default="UNKNOWN")
    commercial_use_allowed = models.CharField(max_length=10, blank=True, default="UNKNOWN")
    source_url = models.CharField(max_length=500, blank=True, default="")
    notes = models.TextField(blank=True, default="")

    class Meta:
        unique_together = ("organization", "code", "version")

    def __str__(self):
        return f"{self.code} {self.version}"


class TestDefinition(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    instrument = models.ForeignKey(Instrument, on_delete=models.PROTECT)
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    language = models.CharField(max_length=20, default="en")
    json_schema = models.JSONField()
    scoring_spec = models.JSONField()
    version = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("organization", "code", "version", "language")

    def __str__(self):
        return f"{self.code} ({self.language})"


class Panel(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("organization", "code")

    def __str__(self):
        return self.code


class PanelItem(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    panel = models.ForeignKey(Panel, on_delete=models.CASCADE)
    test = models.ForeignKey(TestDefinition, on_delete=models.PROTECT)
    order_index = models.IntegerField(default=0)

    class Meta:
        unique_together = ("organization", "panel", "test")
