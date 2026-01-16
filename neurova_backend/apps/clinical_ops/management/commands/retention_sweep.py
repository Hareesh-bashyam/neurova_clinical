from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.clinical_ops.models import AssessmentOrder
from apps.clinical_ops.models_deletion import DeletionRequest

class Command(BaseCommand):
    help = "Mark expired records for deletion"

    def handle(self, *args, **kwargs):
        now = timezone.now()
        qs = AssessmentOrder.objects.filter(
            deletion_status="ACTIVE",
            data_retention_until__lt=now
        )

        for order in qs:
            DeletionRequest.objects.get_or_create(
                org=order.org,
                order=order,
                requested_by="SYSTEM",
                defaults={"reason":"Retention period expired"}
            )
