import re

from backend.clinical.reporting.pdf_renderer_v1 import (
    render_pdf_from_report_json_v1
)


def _sample_report(has_flag: bool, signed: bool):
    return {
        "report_id": "11111111-1111-1111-1111-111111111111",
        "report_type": "PSYCHIATRIC_ASSESSMENT",
        "battery_code": "DEP_SCREEN_V1",
        "battery_version": "1.0",
        "organization": {"name": "Org Name", "address": "Org Address"},
        "patient": {
            "name": "Postman Test Patient",
            "age": 30,
            "gender": "Male",
            "patient_id": "P-001",
        },
        "encounter": {
            "type": "OPD",
            "administration_mode": "IN_CLINIC",
            "date_time": "2026-01-08T23:12:00Z",
        },
        "assessment_summary": {
            "rows": [
                {
                    "test_code": "PHQ9",
                    "test_name": "PHQ-9",
                    "score": 25,
                    "severity": "Severe",
                }
            ],
            "red_flag_present": has_flag,
        },
        "tests": [
            {
                "test_code": "PHQ9",
                "test_name": "PHQ-9",
                "test_version": "1.0",
                "score": 25,
                "severity": "Severe",
                "score_range": "20–27",
                "reference": "0–27",
                "interpretation_text_key": "GENERIC_INTERPRETATION",
                "red_flags": ["SUICIDE_RISK"] if has_flag else [],
            }
        ],
        "safety": {
            "has_flags": has_flag,
            "flags": [
                {
                    "flag_code": "SUICIDE_RISK",
                    "title_key": "SAFETY_TITLE",
                    "body_key": "SAFETY_SUICIDE_BODY",
                }
            ]
            if has_flag
            else [],
        },
        "interpretation_notes": {
            "body_key": "CLINICAL_INTERPRETATION_NOTES"
        },
        "clinical_signoff": {
            "required": True,
            "status": "SIGNED" if signed else "PENDING",
            "reviewed_by": {
                "name": "Dr X",
                "role": "Psychiatrist",
                "registration_number": "REG123",
            }
            if signed
            else {"name": "", "role": "", "registration_number": ""},
            "reviewed_at": "2026-01-08T23:15:00Z" if signed else None,
        },
        "legal": {
            "disclaimer_key": "LEGAL_DISCLAIMER",
            "disclaimer_version": "1.0",
        },
        "traceability": {
            "battery_code": "DEP_SCREEN_V1",
            "battery_version": "1.0",
            "test_versions": [
                {"test_code": "PHQ9", "test_version": "1.0"}
            ],
            "generated_by": "NeurovaX Clinical Engine",
            "generated_at": "2026-01-08T23:12:01Z",
        },
    }


def test_pdf_is_generated():
    pdf_bytes = render_pdf_from_report_json_v1(
        _sample_report(has_flag=False, signed=False)
    )
    assert pdf_bytes[:4] == b"%PDF"


def test_pdf_does_not_leak_internal_strings():
    pdf_bytes = render_pdf_from_report_json_v1(
        _sample_report(has_flag=True, signed=True)
    )
    txt = pdf_bytes.decode("latin-1", errors="ignore")

    forbidden = [
        "Engine Version",
        "Schema Version",
        "Session ID",
    ]
    for f in forbidden:
        assert f not in txt


def test_signed_report_contains_signature_placeholder():
    pdf_bytes = render_pdf_from_report_json_v1(
        _sample_report(has_flag=False, signed=True)
    )
    txt = pdf_bytes.decode("latin-1", errors="ignore")

    assert "Digital Signature: [SIGNATURE_PLACEHOLDER]" in txt


def test_unsigned_report_contains_exact_sentence():
    pdf_bytes = render_pdf_from_report_json_v1(
        _sample_report(has_flag=False, signed=False)
    )
    txt = pdf_bytes.decode("latin-1", errors="ignore")

    assert (
        "This report has been system-validated and has not undergone individual clinical review."
        in txt
    )
