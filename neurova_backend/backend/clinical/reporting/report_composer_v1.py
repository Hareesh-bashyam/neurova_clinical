import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


# -----------------------------
# Section model (DO NOT CHANGE)
# -----------------------------
@dataclass(frozen=True)
class Section:
    key: str
    title: Optional[str]
    lines: List[str]
    table: Optional[Dict[str, Any]] = None


# -----------------------------
# Helpers
# -----------------------------
def _safe(v: Any) -> str:
    return "" if v is None else str(v)


def _cap(s: str) -> str:
    if not s:
        return ""
    if s.isupper():
        return s
    return " ".join(w.capitalize() for w in s.replace("_", " ").split())


def _require(obj: Dict[str, Any], key: str):
    if key not in obj:
        raise ValueError(f"Missing required field: {key}")
    return obj[key]


def _load_text_registry() -> Dict[str, str]:
    base_dir = os.path.dirname(__file__)
    path = os.path.join(base_dir, "report_text_v1.json")
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return json.load(f)


# -----------------------------
# MAIN COMPOSER (V1 – FROZEN)
# -----------------------------
def compose_sections_v1(report_json: Dict[str, Any]) -> List[Section]:
    sections: List[Section] = []
    text_registry = _load_text_registry()

    # -------------------------
    # REQUIRED TOP-LEVEL BLOCKS
    # -------------------------
    org = _require(report_json, "organization")
    patient = _require(report_json, "patient")
    encounter = _require(report_json, "encounter")
    battery = _require(report_json, "battery")
    meta = _require(report_json, "meta")

    # -------------------------
    # 1) HEADER
    # -------------------------
    sections.append(
        Section(
            key="HEADER",
            title=None,
            lines=[
                _safe(org.get("name")),
                _safe(org.get("address")),
                "",
                "Psychiatric Assessment Report",
                f"Report ID: {_safe(report_json.get('report_id'))}",
                f"Report Date/Time: {_safe(meta.get('generated_at'))}",
            ],
        )
    )

    # -------------------------
    # 2) PATIENT & ENCOUNTER
    # -------------------------
    sections.append(
        Section(
            key="PATIENT_DETAILS",
            title="Patient & Encounter Details",
            lines=[
                f"Patient Name: {_safe(patient.get('full_name'))}",
                f"Age / Gender: {_safe(patient.get('age_years'))} / {_safe(patient.get('gender'))}",
                f"Encounter Type: {_cap(encounter.get('type'))}",
                f"Assessment Battery: {_safe(battery.get('battery_code'))}",
                f"Mode of Administration: {_cap(encounter.get('administration_mode'))}",
                f"Assessment Date/Time: {_safe(encounter.get('assessment_date'))}",
            ],
        )
    )

    # -------------------------
    # 3) ASSESSMENT SUMMARY
    # -------------------------
    summary = _require(report_json, "assessment_summary")
    table_rows: List[List[str]] = []

    for r in summary.get("rows", []):
        table_rows.append([
            _safe(r.get("test_name") or r.get("test_code")),
            _safe(r.get("score")),
            _cap(_safe(r.get("severity"))),
        ])

    sections.append(
        Section(
            key="ASSESSMENT_SUMMARY",
            title="Assessment Summary",
            lines=[],
            table={
                "headers": ["Test", "Score", "Severity / Risk Band"],
                "rows": table_rows,
            },
        )
    )

    # -------------------------
    # 4) INDIVIDUAL TEST RESULTS
    # -------------------------
    test_lines: List[str] = []

    for t in report_json.get("tests", []):
        interpretation_key = t.get("interpretation_text_key") or "GENERIC_INTERPRETATION"
        interpretation_text = text_registry.get(interpretation_key, "")

        test_lines.extend([
            f"{_safe(t.get('test_name') or t.get('test_code'))}",
            f"Total Score: {_safe(t.get('score'))}",
            f"Severity / Risk Category: {_cap(_safe(t.get('severity')))}",
            f"Reference Range: {_safe(t.get('score_range'))}",
            interpretation_text,
            "",
        ])

    sections.append(
        Section(
            key="TEST_DETAILS",
            title="Individual Test Results",
            lines=test_lines,
        )
    )

    # -------------------------
    # 5) SAFETY FLAGS (OPTIONAL)
    # -------------------------
    safety = report_json.get("safety_flags", {})
    if safety.get("present"):
        safety_lines = [
            text_registry.get("SAFETY_TITLE", "Important Safety Information"),
        ]
        for desc in safety.get("descriptions", []):
            safety_lines.append(desc)
        safety_lines.append(safety.get("mandatory_instruction", ""))
        safety_lines.append(safety.get("crisis_resource", ""))

        sections.append(
            Section(
                key="SAFETY_FLAGS",
                title="Important Safety Information",
                lines=safety_lines,
            )
        )

    # -------------------------
    # 6) CLINICAL INTERPRETATION NOTES
    # -------------------------
    sections.append(
        Section(
            key="INTERPRETATION_NOTES",
            title="Clinical Interpretation Notes",
            lines=[
                text_registry.get(
                    "CLINICAL_INTERPRETATION_NOTES", ""
                )
            ],
        )
    )

    # -------------------------
    # 7) CLINICAL SIGN-OFF
    # -------------------------
    signoff = report_json.get("clinical_signoff", {
        "status": "SYSTEM_VALIDATED"
    })

    signoff_lines: List[str] = []

    if signoff.get("status") == "SIGNED":
        rb = signoff.get("reviewed_by", {})
        signoff_lines.extend([
            f"Reviewed by: {_safe(rb.get('name'))}",
            f"Role: {_safe(rb.get('role'))}",
            f"Registration Number: {_safe(rb.get('registration_number'))}",
            f"Reviewed at: {_safe(signoff.get('reviewed_at'))}",
            "Digital Signature: [SIGNED]",
        ])
    else:
        signoff_lines.append(
            "This report has been system-validated and has not undergone individual clinical review."
        )

    sections.append(
        Section(
            key="SIGNOFF",
            title="Clinical Responsibility & Sign-off",
            lines=signoff_lines,
        )
    )


    # -------------------------
    # 8) LEGAL DISCLAIMER
    # -------------------------
    sections.append(
        Section(
            key="LEGAL",
            title="Legal Disclaimer",
            lines=[
                text_registry.get("LEGAL_DISCLAIMER", "")
            ],
        )
    )

    # -------------------------
    # 9) FOOTER
    # -------------------------
    trace = _require(report_json, "traceability")
    test_versions = trace.get("test_versions", [])
    tv = ", ".join(
        f"{t['test_code']}:{t['test_version']}" for t in test_versions
    )

    sections.append(
        Section(
            key="FOOTER",
            title=None,
            lines=[
                f"Report ID: {_safe(report_json.get('report_id'))}",
                f"Battery: {_safe(battery.get('battery_code'))} v{_safe(battery.get('battery_version'))}",
                f"Test Versions: {tv}",
                f"Generated by: {_safe(trace.get('generated_by'))}",
                f"Generated at: {_safe(trace.get('generated_at'))}",
                
            ],
        )
    )

    return sections
