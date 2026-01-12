import uuid
from django.utils import timezone
from backend.clinical.models import ClinicalOrder, BatterySession, TestRun, ClinicalReport
from backend.clinical.batteries.battery_runner import get_battery_def
from backend.clinical.scoring.scoring_engine import (
    evaluate_phq9, calculate_sum, calculate_reverse_sum, apply_severity,
    evaluate_mdq, evaluate_asrs
)
import json, os
from reports.models import ClinicalReport
from core.models import Organization


def _load_severity_maps():
    path = os.path.join(os.path.dirname(__file__), "..", "scoring", "severity_maps.json")
    path = os.path.normpath(path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

SEVERITY_MAPS = None

def _severity_label(test_code, score):
    global SEVERITY_MAPS
    if SEVERITY_MAPS is None:
        SEVERITY_MAPS = _load_severity_maps()
    return apply_severity(score, SEVERITY_MAPS[test_code])

def _score_range_str(test_code, severity_label):
    # Hard-map ranges to strings for V1 to avoid dict prints in PDF
    maps = {
        "PHQ9": {
            "Minimal":"0–4","Mild":"5–9","Moderate":"10–14","Moderately Severe":"15–19","Severe":"20–27"
        },
        "GAD7": {"Minimal":"0–4","Mild":"5–9","Moderate":"10–14","Severe":"15–21"},
        "PSS10": {"Low Stress":"0–13","Moderate Stress":"14–26","High Stress":"27–40"},
        "AUDIT": {"Low Risk":"0–7","Hazardous":"8–15","Harmful":"16–19","Possible Dependence":"20–40"},
        "STOP_BANG": {"Low Risk":"0–2","Intermediate Risk":"3–4","High Risk":"5–8"}
    }
    return maps.get(test_code, {}).get(severity_label, "")

def _reference_range(test_code):
    refs = {"PHQ9":"0–27","GAD7":"0–21","PSS10":"0–40","AUDIT":"0–40","STOP_BANG":"0–8"}
    return refs.get(test_code, "")

def _test_name(test_code):
    names = {
        "PHQ9":"PHQ-9","GAD7":"GAD-7","PSS10":"PSS-10",
        "AUDIT":"AUDIT","STOP_BANG":"STOP-BANG","MDQ":"MDQ","ASRS_V1_1":"ASRS v1.1"
    }
    return names.get(test_code, test_code)

def generate_report_for_order_v1(order: ClinicalOrder) -> ClinicalReport:
    """
    V1 Canonical Report Generator
    IMMUTABLE after first generation
    """

    # 🔒 HARD IMMUTABILITY LOCK — FIRST LINE
    existing = ClinicalReport.objects.filter(order=order).first()
    if existing:
        return existing

    # Preconditions
    session = (
        BatterySession.objects
        .filter(order=order)
        .order_by("-created_at")
        .first()
    )
    if not session or session.status != "COMPLETED":
        raise ValueError("Session not completed; cannot generate report")

    battery = get_battery_def(order.battery_code)

    runs = list(
        TestRun.objects
        .filter(session=session)
        .order_by("test_order_index")
    )

    if len(runs) != len(battery["tests"]):
        raise ValueError("Not all tests completed for battery")

    # 🔑 REAL ORGANIZATION (NO PLACEHOLDERS)
    from core.models import Organization
    try:
        org = Organization.objects.get(id=order.organization_id)
    except Organization.DoesNotExist:
        raise ValueError("Organization missing for report generation")

    red_flag_present = False
    summary_rows = []
    tests_out = []
    safety_flags = []

    for tr in runs:
        test_code = tr.test_code
        flags = []

        if test_code == "PHQ9":
            score, suicide_flag = evaluate_phq9(tr.raw_responses)
            severity = _severity_label("PHQ9", score)
            if suicide_flag:
                flags.append("SUICIDE_RISK")

        elif test_code == "GAD7":
            score = calculate_sum(tr.raw_responses)
            severity = _severity_label("GAD7", score)

        elif test_code == "PSS10":
            score = calculate_reverse_sum(tr.raw_responses, reverse_items=[4,5,7,8])
            severity = _severity_label("PSS10", score)

        elif test_code == "AUDIT":
            score = calculate_sum(tr.raw_responses)
            severity = _severity_label("AUDIT", score)

        elif test_code == "STOP_BANG":
            score = calculate_sum(tr.raw_responses)
            severity = _severity_label("STOP_BANG", score)

        elif test_code == "MDQ":
            rr = tr.raw_responses
            result = evaluate_mdq(
                rr["symptom_yes_count"],
                rr["co_occur"],
                rr["impairment"]
            )
            score = None
            severity = "Positive" if result == "POSITIVE" else "Negative"

        elif test_code == "ASRS_V1_1":
            rr = tr.raw_responses
            result = evaluate_asrs(rr["part_a_positive_count"])
            score = None
            severity = "Positive" if result == "POSITIVE" else "Negative"

        else:
            raise ValueError(f"Unknown test_code: {test_code}")

        if flags:
            red_flag_present = True
            if "SUICIDE_RISK" in flags:
                safety_flags.append({
                    "flag_code": "SUICIDE_RISK",
                    "title_key": "SAFETY_TITLE",
                    "body_key": "SAFETY_SUICIDE_BODY"
                })

        tr.computed_score = score
        tr.severity = severity
        tr.reference = _reference_range(test_code)
        tr.score_range = (
            _score_range_str(test_code, severity)
            if score is not None else ""
        )
        tr.red_flags = flags
        tr.save(update_fields=[
            "computed_score",
            "severity",
            "reference",
            "score_range",
            "red_flags"
        ])

        summary_rows.append({
            "test_code": test_code,
            "test_name": _test_name(test_code),
            "score": score if score is not None else "",
            "severity": severity
        })

        tests_out.append({
            "test_code": test_code,
            "test_name": _test_name(test_code),
            "test_version": tr.test_version,
            "score": score if score is not None else "",
            "severity": severity,
            "score_range": tr.score_range,
            "reference": tr.reference,
            "interpretation_text_key": "GENERIC_INTERPRETATION",
            "red_flags": flags
        })

    now = timezone.now().isoformat()
    report_id = str(uuid.uuid4())

    report_json = {
        "report_id": report_id,
        "report_type": "PSYCHIATRIC_ASSESSMENT",
        "battery_code": order.battery_code,
        "battery_version": order.battery_version,

        "organization": {
            "name": org.name,
            "address": org.address or ""
        },

        "patient": {
            "name": order.patient_name,
            "age": order.patient_age,
            "gender": order.patient_gender,
            "patient_id": str(order.patient_id) if order.patient_id else ""
        },

        "encounter": {
            "type": order.encounter_type,
            "administration_mode": order.administration_mode,
            "date_time": now
        },

        "assessment_summary": {
            "rows": summary_rows,
            "red_flag_present": red_flag_present
        },

        "tests": tests_out,

        "safety": {
            "has_flags": red_flag_present,
            "flags": safety_flags
        },

        "interpretation_notes": {
            "body_key": "CLINICAL_INTERPRETATION_NOTES"
        },

        "clinical_signoff": {
            "required": battery["signoff_required"],
            "status": "PENDING" if battery["signoff_required"] else "NOT_REQUIRED",
            "reviewed_by": {
                "name": "",
                "role": "",
                "registration_number": ""
            },
            "reviewed_at": None
        },

        "legal": {
            "disclaimer_key": "LEGAL_DISCLAIMER",
            "disclaimer_version": "1.0"
        },

        "traceability": {
            "battery_code": order.battery_code,
            "battery_version": order.battery_version,
            "test_versions": [
                {"test_code": t["test_code"], "test_version": t["test_version"]}
                for t in tests_out
            ],
            "generated_by": "NeurovaX Clinical Engine",
            "generated_at": now
        }
    }

    return ClinicalReport.objects.create(
        organization_id=order.organization_id,
        order=order,
        report_json=report_json,
        status="GENERATED"
    )
