from django.utils import timezone
from apps.clinical_ops.models_deletion import DeletionRequest
from apps.clinical_ops.models_assessment import AssessmentResponse, AssessmentResult
from apps.clinical_ops.models_report import AssessmentReport
from apps.clinical_ops.audit.logger import log_event

def execute_deletion(dr: DeletionRequest):
    order = dr.order

    # Hard delete clinical payloads
    AssessmentResponse.objects.filter(order=order).delete()
    AssessmentResult.objects.filter(order=order).delete()
    AssessmentReport.objects.filter(order=order).delete()

    # Mark order as deleted (retain shell for audit)
    order.deletion_status = "DELETED"
    order.save(update_fields=["deletion_status"])

    dr.status = "EXECUTED"
    dr.processed_at = timezone.now()
    dr.save(update_fields=["status", "processed_at"])

    log_event(
        org=order.org,
        event_type="DATA_DELETION_EXECUTED",
        entity_type="AssessmentOrder",
        entity_id=order.id,
        actor_role="System",
        details={"reason": dr.reason}
    )
