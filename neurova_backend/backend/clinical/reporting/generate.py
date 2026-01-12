from datetime import datetime
from django.utils import timezone
from django.core.exceptions import ValidationError

from backend.clinical.models import TestRun
from core.models import Organization
from auditlogs.utils import log_event


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def _require(value, message: str):
    if value is None or value == "":
        raise ValidationError(message)
    return value


def _cap(s: str) -> str:
    if not s:
        return ""
    return " ".join(w.capitalize() for w in s.replace("_", " ").split())


def _iso(dt):
    return dt.isoformat() if dt else None


# -------------------------------------------------
# FINAL REPORT GENERATOR (V1 – FROZEN)
# -------------------------------------------------
def generate_report_for_order_v1(order):
    """
    Generates an immutable, canonical V1 report_json.
    MUST FAIL if required data is missing.
    PDF renderer MUST read ONLY from returned report_json.
    """

    # -------------------------
    # ORGANIZATION (NO HARDCODE)
    # -------------------------
    def build_organization_block(org: Organization) -> dict:
        return {
            "name": _require(org.name, "Organization name is required"),
            "code": org.code,
            "org_type": org.org_type,
            "address": org.address or "",
            "signature_required": org.signature_required,
            "default_release_policy": org.default_release_policy,
        }

    org = Organization.objects.filter(id=order.organization_id).first()
    if not org:
        raise ValidationError("Organization not found")

    organization_block = build_organization_block(org)

    # -------------------------
    # SESSION (MUST EXIST + COMPLETED)
    # -------------------------
    session = getattr(order, "session", None)
    if not session:
        raise ValidationError("No session found for order")

    if session.status != "COMPLETED":
        raise ValidationError("Session must be COMPLETED before report generation")

    # -------------------------
    # PATIENT (STRICT – FROM PATIENT MODEL)
    # -------------------------
    patient = getattr(order, "patient", None)
    if not patient:
        raise ValidationError("Patient not linked to order")

    # Required fields
    _require(patient.full_name, "Patient full name is required")
    _require(patient.gender, "Patient gender is required")

    # Age handling (DOB preferred, age frozen)
    if hasattr(patient, "dob") and patient.dob:
        today = timezone.now().date()
        age_years = today.year - patient.dob.year - (
            (today.month, today.day) < (patient.dob.month, patient.dob.day)
        )
    else:
        _require(getattr(patient, "age", None), "Patient age is required")
        age_years = patient.age

    if not (1 <= age_years <= 120):
        raise ValidationError("Patient age must be between 1 and 120")

    if patient.gender not in ["Male", "Female", "Other", "Unknown"]:
        raise ValidationError("Invalid patient gender")

    patient_block = {
        "patient_id": str(patient.id),
        "full_name": patient.full_name,
        "age_years": age_years,
        "gender": patient.gender,
    }

    # -------------------------
    # ENCOUNTER (FROZEN DATE)
    # -------------------------
    if not session.completed_at:
        raise ValidationError("Session completed_at missing")

    encounter_block = {
        "type": _cap(order.encounter_type),
        "administration_mode": order.administration_mode,
        "assessment_date": _iso(session.completed_at),
    }

    # -------------------------
    # TEST RUNS (SERVER ORDER ENFORCED)
    # -------------------------
    test_runs = (
        TestRun.objects
        .filter(session=session, status="COMPLETED")
        .order_by("test_order_index")
    )

    if not test_runs.exists():
        raise ValidationError("No completed test runs found")

    assessment_rows = []
    tests_block = []
    battery_sequence = []

    for tr in test_runs:
        if tr.computed_score is None or tr.severity is None:
            raise ValidationError(f"Missing score for test {tr.test_code}")

        battery_sequence.append(tr.test_code)

        assessment_rows.append({
            "test_code": tr.test_code,
            "test_name": tr.test_name or tr.test_code,
            "score": tr.computed_score,
            "severity": tr.severity,
        })

        tests_block.append({
            "test_code": tr.test_code,
            "test_name": tr.test_name or tr.test_code,
            "score": tr.computed_score,
            "severity": tr.severity,
            "interpretation_text_key": tr.interpretation_text_key,
        })

    # -------------------------
    # BATTERY (IMMUTABLE + ENFORCED)
    # -------------------------
    battery_block = {
        "battery_code": order.battery_code,
        "sequence_enforced": True,
        "resume_supported": True,
        "sequence": battery_sequence,
    }

    # -------------------------
    # FINAL REPORT JSON (V1 – CANONICAL)
    # -------------------------
    report_json = {
        "meta": {
            "schema_version": "v1",
            "engine_version": "v1.0.0",
            "immutable": True,
            "generated_at": _iso(timezone.now()),
        },

        "report_id": str(order.id),

        "organization": organization_block,
        "patient": patient_block,
        "encounter": encounter_block,
        "battery": battery_block,

        "assessment_summary": {
            "rows": assessment_rows
        },

        "tests": tests_block,

        "legal": {
            "disclaimer_key": "CLINICAL_DISCLAIMER_V1"
        },

        "traceability": {
            "generated_by": "Neurova Clinical Engine",
            "generated_at": _iso(timezone.now())
        },

        "footer": {
            "text": "Page {PAGE_NO}"
        }
    }

    # -------------------------
    # AUDIT LOG (MANDATORY)
    # -------------------------
    log_event(
        event="REPORT_GENERATED",
        entity_id=order.id,
        metadata={
            "schema_version": "v1",
            "battery_code": order.battery_code,
        }
    )

    return report_json
