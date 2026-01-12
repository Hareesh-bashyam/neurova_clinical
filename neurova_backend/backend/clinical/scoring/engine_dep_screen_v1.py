# backend/clinical/scoring/engine_dep_screen_v1.py

def _validate_array(raw_responses, expected_len, test_code):
    if not isinstance(raw_responses, list):
        raise ValueError(f"{test_code}: raw_responses must be a list")
    if len(raw_responses) != expected_len:
        raise ValueError(
            f"{test_code}: expected {expected_len} responses, got {len(raw_responses)}"
        )
    for v in raw_responses:
        if not isinstance(v, int) or v < 0 or v > 3:
            raise ValueError(
                f"{test_code}: responses must be integers between 0 and 3"
            )


def score_phq9(raw_responses):
    """
    PHQ-9 scoring
    """
    _validate_array(raw_responses, 9, "PHQ9")

    total = sum(raw_responses)

    if total <= 4:
        severity = "MINIMAL"
        interpretation = "Minimal depressive symptoms"
    elif total <= 9:
        severity = "MILD"
        interpretation = "Mild depressive symptoms"
    elif total <= 14:
        severity = "MODERATE"
        interpretation = "Moderate depressive symptoms"
    elif total <= 19:
        severity = "MODERATELY_SEVERE"
        interpretation = "Moderately severe depressive symptoms"
    else:
        severity = "SEVERE"
        interpretation = "Severe depressive symptoms"

    return {
        "test_code": "PHQ9",
        "raw_score": total,
        "severity": severity,
        "interpretation": interpretation,
    }


def score_gad7(raw_responses):
    """
    GAD-7 scoring
    """
    _validate_array(raw_responses, 7, "GAD7")

    total = sum(raw_responses)

    if total <= 4:
        severity = "MINIMAL"
        interpretation = "Minimal anxiety symptoms"
    elif total <= 9:
        severity = "MILD"
        interpretation = "Mild anxiety symptoms"
    elif total <= 14:
        severity = "MODERATE"
        interpretation = "Moderate anxiety symptoms"
    else:
        severity = "SEVERE"
        interpretation = "Severe anxiety symptoms"

    return {
        "test_code": "GAD7",
        "raw_score": total,
        "severity": severity,
        "interpretation": interpretation,
    }


# -------------------------------------------------
# Battery-level dispatcher (DEP_SCREEN_V1)
# -------------------------------------------------

def score_dep_screen_v1(test_code, raw_responses):
    """
    Entry point for DEP_SCREEN_V1 battery.
    Returns a dict compatible with report_schema_v1.tests[]
    """
    if test_code == "PHQ9":
        return score_phq9(raw_responses)
    elif test_code == "GAD7":
        return score_gad7(raw_responses)
    else:
        raise ValueError(f"Unsupported test_code: {test_code}")
