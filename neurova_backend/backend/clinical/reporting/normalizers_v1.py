from datetime import date, datetime
from typing import Dict, List
from scoring.models import Score
from sessions.models import SessionConsent


def normalize_organization(org):
    address = getattr(org, "address", None)
    return {
        "name": org.name,
        "address": address or "Not Provided",  # REQUIRED by schema
    }



def normalize_patient(patient):
    age_years = "N/A"
    if patient.dob:
        today = date.today()
        # Calculate age properly accounting for leap years
        age_years = (
            today.year
            - patient.dob.year
            - ((today.month, today.day) < (patient.dob.month, patient.dob.day))
        )

    return {
        "name": patient.name,
        "age": age_years,
        "gender": patient.sex or "Not Provided",
        "patient_id": patient.external_id,
    }


def normalize_encounter(session):
    """
    Determine encounter administration mode from consent source.
    Canonical V1 mapping (DO NOT CHANGE casually).
    """

    administration_mode = "IN_PERSON"  # safe default

    try:
        consent = session.consent
        source = consent.source

        if source in {"MOBILE", "REMOTE"}:
            administration_mode = "REMOTE"
        elif source == "KIOSK":
            administration_mode = "IN_PERSON"

    except SessionConsent.DoesNotExist:
        # No consent record → assume in-person
        pass

    return {
        "type": "OUTPATIENT",
        "administration_mode": administration_mode,
        "date_time": session.created_at.isoformat() + "Z",
    }


def normalize_signoff(org):
    return {
        "required": bool(org.signature_required),
        "status": "PENDING",
        "reviewed_by": None,
        "reviewed_at": None,
    }


def normalize_test_results(score_obj) -> Dict:
    score_range = {
        "min": 0,
        "max": 27,
    }

    test = {
        "test_code": "PRIMARY_ASSESSMENT",
        "test_name": "Primary Psychological Assessment",
        "test_version": "1.0",

        "score": score_obj.score,
        "severity": score_obj.severity,

        "score_range": score_range,
        "reference": "Standardized clinical reference",

        "interpretation_text_key": "PRIMARY_ASSESSMENT_INTERPRETATION",
        "red_flags": [],

        "breakdown": score_obj.breakdown or {},
    }

    return {
        "tests": [test],

        "summary_rows": [
            {
                "test_code": "PRIMARY_ASSESSMENT",
                "test_name": "Primary Psychological Assessment",
                "score": score_obj.score,
                "severity": score_obj.severity,
            }
        ],

        "test_versions": [
            {
                "test_code": "PRIMARY_ASSESSMENT",
                "test_version": "1.0",
            }
        ],
    }
