"""
Clinical Scoring Adapter
========================

This module scores all supported clinical tests and batteries.

SUPPORTED TESTS
- PHQ9
- GAD7
- MDQ
- PSS10
- AUDIT
- STOP_BANG

SUPPORTED BATTERIES
- DEP_SCREEN_V1
- ANX_SCREEN_V1
- STRESS_BURNOUT_V1
- SLEEP_RISK_V1
- SUBSTANCE_SCREEN_V1
- CMHA_V1
- MOOD_RISK_V1
- EWB_INDEX_V1
- MENTAL_HEALTH_CORE_V1
"""


# --------------------------------------------------
# BATTERY → TEST MAPPING
# --------------------------------------------------
BATTERY_TESTS = {
    "DEP_SCREEN_V1": ["PHQ9", "MDQ"],
    "ANX_SCREEN_V1": ["GAD7"],
    "STRESS_BURNOUT_V1": ["PSS10"],
    "SLEEP_RISK_V1": ["STOP_BANG"],
    "SUBSTANCE_SCREEN_V1": ["AUDIT"],
    "CMHA_V1": ["PHQ9", "MDQ", "GAD7", "PSS10", "AUDIT", "STOP_BANG"],
    "MOOD_RISK_V1": ["PHQ9", "MDQ"],
    "EWB_INDEX_V1": ["PHQ9", "GAD7", "PSS10"],
    "MENTAL_HEALTH_CORE_V1": ["PHQ9", "GAD7"],
}


# --------------------------------------------------
# QUESTION → TEST RESOLVER
# --------------------------------------------------
def infer_test_from_question_id(question_id: str) -> str:
    q = question_id.lower()

    if q.startswith("phq9_"):
        return "PHQ9"
    if q.startswith("gad7_"):
        return "GAD7"
    if q.startswith("mdq_"):
        return "MDQ"
    if q.startswith("pss10_"):
        return "PSS10"
    if q.startswith("audit_"):
        return "AUDIT"
    if q.startswith("stop_bang_"):
        return "STOP_BANG"

    raise ValueError(f"Unknown question_id: {question_id}")


# --------------------------------------------------
# INDIVIDUAL TEST SCORING
# --------------------------------------------------

def score_phq9(answers):
    score = sum(a["value"] for a in answers)

    if score <= 4:
        severity = "MINIMAL"
    elif score <= 9:
        severity = "MILD"
    elif score <= 14:
        severity = "MODERATE"
    elif score <= 19:
        severity = "MODERATELY_SEVERE"
    else:
        severity = "SEVERE"

    suicide_flag = any(
        a["question_id"] == "phq9_q9" and a["value"] > 0
        for a in answers
    )

    return {
        "score": score,
        "severity": severity,
        "suicide_flag": suicide_flag,
    }


def score_gad7(answers):
    score = sum(a["value"] for a in answers)

    if score <= 4:
        severity = "MINIMAL"
    elif score <= 9:
        severity = "MILD"
    elif score <= 14:
        severity = "MODERATE"
    else:
        severity = "SEVERE"

    return {
        "score": score,
        "severity": severity,
    }


def score_mdq(answers):
    yes_count = sum(1 for a in answers if a["value"] == 1)

    clustered = any(
        a["question_id"] == "mdq_cluster" and a["value"] == 1
        for a in answers
    )
    impairment = any(
        a["question_id"] == "mdq_impairment" and a["value"] == 1
        for a in answers
    )

    positive = yes_count >= 7 and clustered and impairment

    return {
        "yes_count": yes_count,
        "positive_screen": positive,
        "severity": "POSITIVE" if positive else "NEGATIVE",
    }


def score_pss10(answers):
    score = sum(a["value"] for a in answers)

    if score <= 13:
        severity = "LOW"
    elif score <= 26:
        severity = "MODERATE"
    else:
        severity = "HIGH"

    return {
        "score": score,
        "severity": severity,
    }


def score_audit(answers):
    score = sum(a["value"] for a in answers)

    if score <= 7:
        risk = "LOW"
    elif score <= 15:
        risk = "HAZARDOUS"
    elif score <= 19:
        risk = "HARMFUL"
    else:
        risk = "DEPENDENCE"

    return {
        "score": score,
        "risk_level": risk,
        "severity": risk,
    }


def score_stop_bang(answers):
    score = sum(a["value"] for a in answers)

    if score <= 2:
        risk = "LOW"
    elif score <= 4:
        risk = "INTERMEDIATE"
    else:
        risk = "HIGH"

    return {
        "score": score,
        "risk_level": risk,
        "severity": risk,
    }


# --------------------------------------------------
# MAIN BATTERY SCORER
# --------------------------------------------------
def score_battery(battery_code: str, battery_version: str, answers_json: dict) -> dict:
    answers = answers_json.get("answers", [])
    if not answers:
        raise ValueError("answers are required")

    expected_tests = BATTERY_TESTS.get(battery_code)
    if not expected_tests:
        raise ValueError(f"Unsupported battery_code: {battery_code}")

    # Group answers by test
    grouped = {}
    for ans in answers:
        test = infer_test_from_question_id(ans["question_id"])
        grouped.setdefault(test, []).append(ans)

    per_test = {}
    red_flags = []

    for test in expected_tests:
        test_answers = grouped.get(test, [])

        if not test_answers:
            raise ValueError(f"Missing answers for test: {test}")

        if test == "PHQ9":
            result = score_phq9(test_answers)
            if result["suicide_flag"]:
                red_flags.append("SUICIDE_RISK")

        elif test == "GAD7":
            result = score_gad7(test_answers)

        elif test == "MDQ":
            result = score_mdq(test_answers)

        elif test == "PSS10":
            result = score_pss10(test_answers)

        elif test == "AUDIT":
            result = score_audit(test_answers)

        elif test == "STOP_BANG":
            result = score_stop_bang(test_answers)

        else:
            raise ValueError(f"Unsupported test: {test}")

        per_test[test] = result

    severity_rank = {
        "LOW": 0,
        "MINIMAL": 0,
        "NEGATIVE": 0,
        "MILD": 1,
        "MODERATE": 2,
        "HIGH": 3,
        "MODERATELY_SEVERE": 4,
        "SEVERE": 5,
        "DEPENDENCE": 6,
        "POSITIVE": 6,
    }

    primary_severity = max(
        (v.get("severity") for v in per_test.values()),
        key=lambda s: severity_rank.get(s, 0),
    )

    return {
        "battery_code": battery_code,
        "battery_version": battery_version,
        "per_test": per_test,
        "summary": {
            "primary_severity": primary_severity,
            "has_red_flags": bool(red_flags),
            "red_flags": red_flags,
        },
    }
