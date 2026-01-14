from django.utils import timezone
from reports.models import ClinicalReport


def apply_clinical_signoff(
    report: ClinicalReport,
    clinician_name: str,
    clinician_role: str,
    registration_number: str,
):
    # ---- idempotency ----
    if report.status == "SIGNED":
        return report

    report_json = report.report_json or {}

    report_json["clinical_signoff"] = {
        "status": "SIGNED",
        "reviewed_by": {
            "name": clinician_name,
            "role": clinician_role,
            "registration_number": registration_number,
        },
        "reviewed_at": timezone.now().isoformat(),
    }

    report.report_json = report_json
    report.status = "SIGNED"
    report.save(update_fields=["report_json", "status"])

    return report
