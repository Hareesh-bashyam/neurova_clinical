from django.utils.timezone import now
from scoring.models import Score
from safety.models import RedFlagEvent
from reports.models import Report


def build_report_json(*, report: Report) -> dict:
    """
    Build CANONICAL report JSON.
    SINGLE SOURCE OF TRUTH for PDF generation.
    """

    session = report.session
    patient = session.order.patient
    org = report.organization

    scores = Score.objects.filter(session=session)
    flags = RedFlagEvent.objects.filter(session=session)

    tests = []
    red_flag_present = flags.exists()

    for s in scores:
        severity_map = s.scoring_spec.get("severity_thresholds", [])
        score_range = ""

        prev_max = -1
        for t in severity_map:
            max_v = int(t["max"])
            if s.total_score <= max_v:
                score_range = f"{prev_max + 1}–{max_v}"
                break
            prev_max = max_v

        tests.append({
            "test_code": s.test_code,
            "test_version": s.test_version,
            "score": s.total_score,
            "severity": s.severity_band,
            "score_range": score_range,
            "interpretation_key": f"{s.test_code}_{s.severity_band.upper().replace(' ', '_')}",
            "red_flags": [f.flag_type for f in flags],
        })

    return {
        "report_id": report.id,
        "report_type": "PSYCHIATRIC_ASSESSMENT",

        "battery": {
            "code": session.order.panel.code,
            "version": "1.0",
        },

        "organization": {
            "name": org.name,
            "address": "",
        },

        "patient": {
            "name": patient.name,
            "age": None,
            "gender": patient.sex,
            "patient_id": patient.external_id,
        },

        "encounter": {
            "type": "DIAGNOSTIC",
            "administration_mode": "IN_CLINIC",
            "date_time": session.submitted_at.isoformat(),
        },

        "tests": tests,

        "system_notes": {
            "system_validated": True,
            "red_flag_present": red_flag_present,
        },

        "clinical_signoff": {
            "required": org.signature_required,
            "status": "PENDING",
        },

        "audit": {
            "created_at": report.created_at.isoformat(),
            "generated_by": "NeurovaX Clinical Engine",
        },
    }
