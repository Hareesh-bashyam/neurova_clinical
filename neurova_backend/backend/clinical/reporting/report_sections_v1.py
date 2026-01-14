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


# ---------------------------------------
# Text registry (static key -> final text)
# ---------------------------------------
def _load_text_registry() -> Dict[str, str]:
    base_dir = os.path.dirname(__file__)
    path = os.path.join(base_dir, "report_text_v1.json")

    # 🔒 UTF-8 SAFE LOAD (prevents UnicodeDecodeError)
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return json.load(f)


def _get_text(registry: Dict[str, str], key: str) -> str:
    if not key:
        return ""
    return registry.get(key, "")


def _cap(s: str) -> str:
    if not s:
        return ""
    if s.isupper():
        return s
    return " ".join(w.capitalize() for w in s.split())


def _safe_str(v: Any) -> str:
    if v is None:
        return ""
    try:
        return str(v)
    except Exception:
        return ""


# -------------------------------------------------
# MAIN SECTION COMPOSER (FROZEN ORDER — DO NOT EDIT)
# -------------------------------------------------
def compose_sections_v1(report_json: Dict[str, Any]) -> List[Section]:
    registry = _load_text_registry()
    sections: List[Section] = []

    # ---------- SAFE ROOT OBJECTS ----------
    org = report_json.get("organization")
    if not org:
        raise ValueError(
            "Invalid report_json: missing 'organization'. "
            "This report was generated using an older schema. "
            "Please regenerate the report."
        )

    meta = report_json.get("meta")
    if not meta:
        raise ValueError(
            "Invalid report_json: missing 'meta'. "
            "This report was generated using an older schema. "
            "Please regenerate the report."
        )
    encounter = report_json.get("encounter", {})
    trace = report_json.get("traceability", {})

    # -------------------
    # 1) HEADER
    # -------------------
    sections.append(
        Section(
            key="HEADER",
            title=None,
            lines = [
                org["name"],
                org["address"],
                "",
                "Psychiatric Assessment Report",
                f"Report ID: {report_json['report_id']}",
                f"Report Date/Time: {meta['generated_at']}",
]

        )
    )

    # -------------------
    # 2) PATIENT DETAILS
    # -------------------
    sections.append(
        Section(
            key="PATIENT_DETAILS",
            title="Patient & Encounter Details",
            lines=[
                f"Patient Name: {_safe_str(patient.get('name'))}",
                f"Age / Gender: {_safe_str(patient.get('age'))} / {_safe_str(patient.get('gender'))}",
                f"Encounter Type: {_cap(encounter.get('type', ''))}",
                f"Assessment Battery: {_safe_str(report_json.get('battery_code'))}",
                f"Mode of Administration: {_cap(encounter.get('administration_mode', '').replace('_', ' '))}",
                f"Assessment Date/Time: {_safe_str(encounter.get('date_time'))}",
            ],
        )
    )

    # -------------------
    # 3) ASSESSMENT SUMMARY
    # -------------------
    rows = []
    summary = report_json.get("assessment_summary", {})
    for r in summary.get("rows", []):
        rows.append([
            _safe_str(r.get("test_name") or r.get("test_code")),
            _safe_str(r.get("score")),
            _cap(_safe_str(r.get("severity"))),
        ])

    sections.append(
        Section(
            key="ASSESSMENT_SUMMARY",
            title="Assessment Summary",
            lines=[],
            table={
                "headers": ["Test", "Score", "Severity / Risk Band"],
                "rows": rows,
            },
        )
    )

    # -------------------
    # 4) TEST DETAILS
    # -------------------
    detail_lines: List[str] = []
    for t in report_json.get("tests", []):
        detail_lines.extend([
            f"{_safe_str(t.get('test_name'))} ({_safe_str(t.get('test_code'))})",
            f"Total Score: {_safe_str(t.get('score'))}",
            f"Severity: {_cap(_safe_str(t.get('severity')))}",
            _get_text(registry, t.get("interpretation_text_key")),
            "",
        ])

    sections.append(
        Section(
            key="TEST_DETAILS",
            title="Individual Test Results",
            lines=detail_lines,
        )
    )

    # -------------------
    # 5) LEGAL
    # -------------------
    legal = report_json.get("legal", {})
    sections.append(
        Section(
            key="LEGAL",
            title="Legal Disclaimer",
            lines=[_get_text(registry, legal.get("disclaimer_key"))],
        )
    )

    # -------------------
    # 6) FOOTER
    # -------------------
    sections.append(
        Section(
            key="FOOTER",
            title=None,
            lines=[
                f"Generated by: {_safe_str(trace.get('generated_by'))}",
                f"Generated at: {_safe_str(trace.get('generated_at'))}",
                "Page {PAGE_NO} of {PAGE_TOTAL}",
            ],
        )
    )

    return sections
