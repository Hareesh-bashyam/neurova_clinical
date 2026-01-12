import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from .report_schema_v1 import empty_report
from backend.clinical.scoring.engine_v1 import score_phq9

# -----------------------------
# Section model (do not change)
# -----------------------------
@dataclass(frozen=True)
class Section:
    key: str                 # e.g. "HEADER", "PATIENT_DETAILS"
    title: Optional[str]     # None allowed for header/footer
    lines: List[str]         # Already formatted plain text lines
    table: Optional[Dict[str, Any]] = None  # {"headers":[...], "rows":[[...], ...]}


# ---------------------------------------
# Text registry (static key -> final text)
# ---------------------------------------
def _load_text_registry() -> Dict[str, str]:
    base_dir = os.path.dirname(__file__)
    path = os.path.join(base_dir, "report_text_v1.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_text(registry: Dict[str, str], key: str) -> str:
    if key not in registry:
        raise ValueError(f"Missing report_text key: {key}")
    return registry[key]


def _cap(s: str) -> str:
    # Capitalize words for labels like "Severe", "Moderately Severe"
    # If already contains uppercase words like "OPD" keep as is.
    if s.isupper():
        return s
    return " ".join([w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" ")])


def _safe_str(v: Any) -> str:
    if v is None:
        return ""
    return str(v)


def _require(report_json: Dict[str, Any], path: str) -> Any:
    # path format: "patient.name" etc
    parts = path.split(".")
    cur = report_json
    for p in parts:
        if p not in cur:
            raise ValueError(f"Missing required field in report_json: {path}")
        cur = cur[p]
    return cur


def compose_sections_v1(report_json: Dict[str, Any]) -> List[Section]:
    """
    Returns section list in EXACT frozen order:
    1 HEADER
    2 PATIENT_DETAILS
    3 ASSESSMENT_SUMMARY
    4 TEST_DETAILS (repeated blocks, but we keep as one section containing lines)
    5 SAFETY_FLAGS (only if present)
    6 INTERPRETATION_NOTES
    7 SIGNOFF
    8 LEGAL
    9 FOOTER
    """
    registry = _load_text_registry()

    # Validate required top-level structure (hard fail if missing)
    _require(report_json, "report_id")
    _require(report_json, "report_type")
    _require(report_json, "battery_code")
    _require(report_json, "battery_version")
    _require(report_json, "organization.name")
    _require(report_json, "organization.address")
    _require(report_json, "patient.name")
    _require(report_json, "patient.age")
    _require(report_json, "patient.gender")
    _require(report_json, "encounter.type")
    _require(report_json, "encounter.administration_mode")
    _require(report_json, "encounter.date_time")
    _require(report_json, "assessment_summary.rows")
    _require(report_json, "tests")
    _require(report_json, "clinical_signoff.required")
    _require(report_json, "clinical_signoff.status")
    _require(report_json, "legal.disclaimer_key")
    _require(report_json, "traceability.generated_by")
    _require(report_json, "traceability.generated_at")

    sections: List[Section] = []

    # -------------------
    # 1) HEADER (no table)
    # -------------------
    header_lines = [
        _safe_str(report_json["organization"]["name"]),
        _safe_str(report_json["organization"]["address"]),
        "Psychiatric Assessment Report",
        f"Report ID: {_safe_str(report_json['report_id'])}",
        f"Report Date/Time: {_safe_str(report_json['encounter']['date_time'])}",
    ]
    sections.append(Section(key="HEADER", title=None, lines=header_lines, table=None))

    # -----------------------------------
    # 2) PATIENT & ENCOUNTER DETAILS (box)
    # -----------------------------------
    patient_id = _safe_str(report_json["patient"].get("patient_id", ""))

    patient_lines = [
        f"Patient Name: {_safe_str(report_json['patient']['name'])}",
        f"Age / Gender: {_safe_str(report_json['patient']['age'])} / {_safe_str(report_json['patient']['gender'])}",
    ]
    if patient_id:
        patient_lines.append(f"Patient ID: {patient_id}")

    patient_lines.extend([
        f"Encounter Type: {_cap(_safe_str(report_json['encounter']['type']))}",
        f"Assessment Battery: {_safe_str(report_json['battery_code'])}",
        f"Mode of Administration: {_cap(_safe_str(report_json['encounter']['administration_mode']).replace('_',' '))}",
        f"Assessment Date/Time: {_safe_str(report_json['encounter']['date_time'])}",
    ])

    sections.append(Section(
        key="PATIENT_DETAILS",
        title="Patient & Encounter Details",
        lines=patient_lines,
        table=None
    ))

    # ---------------------------
    # 3) ASSESSMENT SUMMARY table
    # ---------------------------
    summary_rows = report_json["assessment_summary"]["rows"]
    table_headers = ["Test", "Score", "Severity / Risk Band"]

    table_rows: List[List[str]] = []
    for row in summary_rows:
        test_name = _safe_str(row.get("test_name") or row.get("test_code"))
        score = _safe_str(row.get("score", ""))
        severity = _cap(_safe_str(row.get("severity", "")))
        table_rows.append([test_name, score, severity])

    sections.append(Section(
        key="ASSESSMENT_SUMMARY",
        title="Assessment Summary",
        lines=[],
        table={"headers": table_headers, "rows": table_rows}
    ))

    # -----------------------------------------
    # 4) INDIVIDUAL TEST RESULTS (text blocks)
    # -----------------------------------------
    tests = report_json["tests"]
    detail_lines: List[str] = []
    for t in tests:
        # required fields per test
        for field in ["test_code", "test_name", "test_version", "score", "severity", "score_range", "reference", "interpretation_text_key", "red_flags"]:
            if field not in t:
                raise ValueError(f"Missing test field {field} in tests[] for {t.get('test_code')}")

        detail_lines.append(f"{_safe_str(t['test_name'])} ({_safe_str(t['test_code'])})")
        detail_lines.append(f"Test Version: {_safe_str(t['test_version'])}")
        detail_lines.append(f"Total Score: {_safe_str(t['score'])}")
        detail_lines.append(f"Severity / Risk Category: {_cap(_safe_str(t['severity']))}")
        detail_lines.append(f"Reference Range: {_safe_str(t['reference'])}")
        detail_lines.append(f"Severity Band Range: {_safe_str(t['score_range'])}")
        detail_lines.append(_get_text(registry, t["interpretation_text_key"]))
        # spacing line
        detail_lines.append("")

    sections.append(Section(
        key="TEST_DETAILS",
        title="Individual Test Results",
        lines=detail_lines,
        table=None
    ))

    # ---------------------------------------
    # 5) SAFETY FLAGS (only if flags present)
    # ---------------------------------------
    has_flags = bool(report_json.get("safety", {}).get("has_flags", False))
    if has_flags:
        flags = report_json["safety"].get("flags", [])
        safety_lines: List[str] = []
        safety_lines.append(_get_text(registry, "SAFETY_TITLE"))
        for fl in flags:
            # flag_code required
            if "flag_code" not in fl:
                raise ValueError("Missing flag_code in safety.flags[]")
            # For V1 we support suicide body key mapping
            # Use body_key field, resolve via registry
            body_key = fl.get("body_key")
            if not body_key:
                raise ValueError(f"Missing body_key for flag {fl['flag_code']}")
            safety_lines.append(_get_text(registry, body_key))
            safety_lines.append("")
        sections.append(Section(
            key="SAFETY_FLAGS",
            title="Important Safety Information",
            lines=safety_lines,
            table=None
        ))

    # ----------------------------
    # 6) INTERPRETATION NOTES text
    # ----------------------------
    notes_key = report_json["interpretation_notes"]["body_key"]
    notes_text = _get_text(registry, notes_key)
    sections.append(Section(
        key="INTERPRETATION_NOTES",
        title="Clinical Interpretation Notes",
        lines=[notes_text],
        table=None
    ))

    # -----------------------
    # 7) SIGNOFF section text
    # -----------------------
    sign = report_json["clinical_signoff"]
    status = _safe_str(sign["status"]).upper()

    sign_lines: List[str] = []
    sign_lines.append(f"Sign-off Required: {'Yes' if sign.get('required') else 'No'}")
    sign_lines.append(f"Sign-off Status: {status}")

    if status == "SIGNED":
        rb = sign.get("reviewed_by") or {}
        sign_lines.append(f"Reviewed by: {_safe_str(rb.get('name',''))}")
        sign_lines.append(f"Role: {_safe_str(rb.get('role',''))}")
        regno = _safe_str(rb.get("registration_number",""))
        if regno:
            sign_lines.append(f"Registration Number: {regno}")
        sign_lines.append(f"Reviewed at: {_safe_str(sign.get('reviewed_at',''))}")
        sign_lines.append("Digital Signature: [SIGNATURE_PLACEHOLDER]")
    else:
        # EXACT required sentence
        sign_lines.append("This report has been system-validated and has not undergone individual clinical review.")

    sections.append(Section(
        key="SIGNOFF",
        title="Clinical Responsibility & Sign-off",
        lines=sign_lines,
        table=None
    ))

    # ------------------------
    # 8) LEGAL DISCLAIMER text
    # ------------------------
    disclaimer_key = report_json["legal"]["disclaimer_key"]
    disclaimer_text = _get_text(registry, disclaimer_key)

    sections.append(Section(
        key="LEGAL",
        title="Legal Disclaimer",
        lines=[disclaimer_text],
        table=None
    ))

    # ----------------
    # 9) FOOTER (trace)
    # ----------------
    # Do NOT show engine version/session id/schema version.
    test_versions = report_json["traceability"].get("test_versions", [])
    tv_str = ", ".join([f"{x['test_code']}:{x['test_version']}" for x in test_versions]) if test_versions else ""

    footer_lines = [
        f"Report ID: {_safe_str(report_json['report_id'])}",
        f"Battery: {_safe_str(report_json['battery_code'])} v{_safe_str(report_json['battery_version'])}",
        f"Test Versions: {tv_str}",
        f"Generated by: {_safe_str(report_json['traceability']['generated_by'])}",
        f"Generated at: {_safe_str(report_json['traceability']['generated_at'])}",
        "Page {PAGE_NO} of {PAGE_TOTAL}"
    ]
    sections.append(Section(key="FOOTER", title=None, lines=footer_lines, table=None))

    return sections


def compose_report_v1(order, session, test_runs):
    report = empty_report(order, session)

    for run in test_runs:
        if run.test_code == "PHQ9":
            scored = score_phq9(run.raw_responses)
            report["tests"].append(scored)

    report["generated_at"] = timezone.now().isoformat()
    return report