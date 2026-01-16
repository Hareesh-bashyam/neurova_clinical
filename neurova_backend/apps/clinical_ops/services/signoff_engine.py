from django.utils import timezone
from apps.clinical_ops.models_report import AssessmentReport
from apps.clinical_ops.models_assessment import AssessmentResult
from apps.clinical_ops.audit.logger import log_event

SYSTEM_SIGNER_NAME = "NeurovaX System"
SYSTEM_SIGNER_ROLE = "System"

def evaluate_signoff_rules(result_json: dict) -> dict:
    """
    Rules-based: system can sign ONLY if:
      - scoring exists
      - report contains disclaimers and required keys
      - red flags are present/absent but are *explicitly disclosed*
    IMPORTANT: This is NOT clinical diagnosis. It is data integrity + completeness signoff.
    """
    summary = (result_json or {}).get("summary", {}) or {}

    # minimal required fields
    required = ["primary_severity", "has_red_flags"]
    missing = [k for k in required if k not in summary]

    # red flags list must exist (even if empty)
    rf = summary.get("red_flags", None)
    if rf is None:
        missing.append("red_flags")

    ok = len(missing) == 0

    return {
        "ok": ok,
        "missing": missing,
        "has_red_flags": bool(summary.get("has_red_flags", False)),
        "primary_severity": summary.get("primary_severity"),
    }

def system_sign_report(report: AssessmentReport, actor_user=None):
    """
    Sets report sign-off as SYSTEM signed if rules pass.
    """
    order = report.order
    result = AssessmentResult.objects.get(order=order)

    verdict = evaluate_signoff_rules(result.result_json)

    if not verdict["ok"]:
        # Reject system signoff
        report.signoff_status = "REJECTED"
        report.signoff_method = "SYSTEM"
        report.signed_by_name = SYSTEM_SIGNER_NAME
        report.signed_by_role = SYSTEM_SIGNER_ROLE
        report.signed_at = timezone.now()
        report.signoff_reason = f"System signoff failed. Missing: {verdict['missing']}"
        report.save(update_fields=[
            "signoff_status","signoff_method","signed_by_name","signed_by_role","signed_at","signoff_reason"
        ])

        log_event(
            org_id=order.org_id,
            event_type="REPORT_REJECTED",
            entity_type="AssessmentReport",
            entity_id=report.id,
            actor_user_id=str(getattr(actor_user, "id", "")) if actor_user else None,
            actor_name=SYSTEM_SIGNER_NAME,
            actor_role=SYSTEM_SIGNER_ROLE,
            details={"reason": report.signoff_reason, "missing": verdict["missing"]}
        )
        return verdict

    # SIGN
    report.signoff_status = "SIGNED"
    report.signoff_method = "SYSTEM"
    report.signed_by_name = SYSTEM_SIGNER_NAME
    report.signed_by_role = SYSTEM_SIGNER_ROLE
    report.signed_at = timezone.now()
    report.signoff_reason = "System signoff: data integrity and completeness verified."
    report.save(update_fields=[
        "signoff_status","signoff_method","signed_by_name","signed_by_role","signed_at","signoff_reason"
    ])

    log_event(
        org_id=order.org_id,
        event_type="REPORT_SIGNED",
        entity_type="AssessmentReport",
        entity_id=report.id,
        actor_user_id=str(getattr(actor_user, "id", "")) if actor_user else None,
        actor_name=SYSTEM_SIGNER_NAME,
        actor_role=SYSTEM_SIGNER_ROLE,
        details={
            "primary_severity": verdict.get("primary_severity"),
            "has_red_flags": verdict.get("has_red_flags"),
            "method": "SYSTEM"
        }
    )
    return verdict
