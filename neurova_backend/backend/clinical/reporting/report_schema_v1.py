from typing import Dict, Any
from datetime import datetime


def build_report_json_v1(
    report_id,
    org,
    patient,
    encounter,
    battery,
    test_results,
    flags,
    signoff
) -> Dict[str, Any]:
    """
    Build canonical immutable V1 clinical report JSON.

    IMPORTANT:
    - This function ONLY assembles JSON.
    - No rendering logic.
    - No DB writes.
    - No engine/session/schema metadata.
    """

    generated_at = datetime.utcnow().isoformat() + "Z"

    return {
        "report_id": str(report_id),
        "report_type": "PSYCHIATRIC_ASSESSMENT",
        "meta": {
            "generated_at": generated_at,
            "schema_version": "v1",
        },
        "battery": {
            "battery_code": battery["code"],
            "battery_version": battery["version"],
        },
        "organization": {
            "name": org["name"],
            "address": org["address"]
        },
        "patient": {
            "name": patient["name"],
            "age": patient["age"],
            "gender": patient["gender"],
            "patient_id": patient.get("patient_id")
        },
        "encounter": {
            "type": encounter["type"],
            "administration_mode": encounter["administration_mode"],
            "date_time": encounter["date_time"]
        },
        "assessment_summary": {
            "rows": test_results["summary_rows"],
            "red_flag_present": bool(flags)
        },
        "tests": test_results["tests"],
        "safety": {
            "has_flags": bool(flags),
            "flags": flags
        },
        "interpretation_notes": {
            "body_key": "CLINICAL_INTERPRETATION_NOTES"
        },
        "clinical_signoff": {
            "required": signoff["required"],
            "status": signoff["status"],
            "reviewed_by": signoff.get("reviewed_by"),
            "reviewed_at": signoff.get("reviewed_at")
        },
        "legal": {
            "disclaimer_key": "LEGAL_DISCLAIMER",
            "disclaimer_version": "1.0"
        },
        "traceability": {
            "battery_code": battery["code"],
            "battery_version": battery["version"],
            "test_versions": test_results["test_versions"],
            "generated_by": "NeurovaX Clinical Engine",
            "generated_at": generated_at
        }
    }

REPORT_SCHEMA_VERSION = "v1"


def empty_report(order, session):
    return {
        "meta": {
            "schema_version": REPORT_SCHEMA_VERSION,
            "engine_version": "v1.0.0",
            "order_id": str(order.id),
            "session_id": str(session.id),
            "battery_code": order.battery_code,
        },
        "patient": {
            "name": order.patient_name,
        },
        "tests": [],
        "summary": {},
        "flags": [],
        "generated_at": None,
    }
