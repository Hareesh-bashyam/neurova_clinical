from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.clinical_ops.models import AssessmentOrder


class Command(BaseCommand):
    help = "Cancel stale/expired assessment orders"

    def handle(self, *args, **options):
        now = timezone.now()

        qs = AssessmentOrder.objects.filter(
            public_link_expires_at__lt=now,
            status__in=[
                AssessmentOrder.STATUS_CREATED,
                AssessmentOrder.STATUS_IN_PROGRESS,
            ],
        )

        count = qs.count()
        qs.update(status=AssessmentOrder.STATUS_CANCELLED)

        self.stdout.write(
            self.style.SUCCESS(f"Cancelled {count} expired orders")
        )
