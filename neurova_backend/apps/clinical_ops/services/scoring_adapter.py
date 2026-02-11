"""
Clinical Scoring Adapter (Production Hardened)
==============================================

Supported Tests:
- PHQ9
- GAD7
- MDQ
- PSS10
- AUDIT
- STOP_BANG
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
# SAFE VALUE PARSER
# --------------------------------------------------

def safe_sum(answers):
    return sum(int(a.get("value", 0) or 0) for a in answers)


# --------------------------------------------------
# INDIVIDUAL TEST SCORING
# --------------------------------------------------

def score_phq9(answers):
    score = safe_sum(answers)

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
        a.get("question_id") == "phq9_q9" and int(a.get("value", 0)) > 0
        for a in answers
    )

    return {
        "score": score,
        "severity": severity,
        "suicide_flag": suicide_flag,
    }


def score_gad7(answers):
    score = safe_sum(answers)

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


MDQ_SYMPTOM_IDS = {
    "mdq_q1", "mdq_q2", "mdq_q3", "mdq_q4", "mdq_q5",
    "mdq_q6", "mdq_q7", "mdq_q8", "mdq_q9", "mdq_q10",
    "mdq_q11", "mdq_q12", "mdq_q13",
}


def score_mdq(answers):

    symptom_answers = [
        a for a in answers
        if a.get("question_id") in MDQ_SYMPTOM_IDS
    ]

    yes_count = sum(
        1 for a in symptom_answers
        if int(a.get("value", 0)) == 1
    )

    clustered = any(
        a.get("question_id") == "mdq_cluster" and int(a.get("value", 0)) == 1
        for a in answers
    )

    impairment = any(
        a.get("question_id") == "mdq_impairment" and int(a.get("value", 0)) >= 2
        for a in answers
    )

    positive = yes_count >= 7 and clustered and impairment

    return {
        "score": yes_count,
        "max_score": 13,
        "yes_count": yes_count,
        "positive_screen": positive,
        "severity": "POSITIVE" if positive else "NEGATIVE",
    }


def score_pss10(answers):
    score = safe_sum(answers)

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
    score = safe_sum(answers)

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
    score = safe_sum(answers)

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
# PRIMARY SEVERITY ENGINE (CLINICALLY SAFE)
# --------------------------------------------------

def calculate_primary_severity(per_test, red_flags):

    # Suicide overrides everything
    if "SUICIDE_RISK" in red_flags:
        return "CRITICAL"

    # High risk triggers
    high_conditions = [
        per_test.get("PHQ9", {}).get("severity") in ["MODERATELY_SEVERE", "SEVERE"],
        per_test.get("AUDIT", {}).get("severity") in ["HARMFUL", "DEPENDENCE"],
        per_test.get("STOP_BANG", {}).get("severity") == "HIGH",
        per_test.get("MDQ", {}).get("positive_screen") is True,
    ]

    if any(high_conditions):
        return "HIGH"

    # Moderate cluster
    if any(
        v.get("severity") == "MODERATE"
        for v in per_test.values()
    ):
        return "MODERATE"

    return "LOW"


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

    grouped = {}
    for ans in answers:
        try:
            test = infer_test_from_question_id(ans.get("question_id", ""))
            grouped.setdefault(test, []).append(ans)
        except ValueError:
            continue  # Ignore unknown questions safely

    per_test = {}
    red_flags = []

    for test in expected_tests:
        test_answers = grouped.get(test, [])
        if not test_answers:
            raise ValueError(f"Missing answers for test: {test}")

        if test == "PHQ9":
            result = score_phq9(test_answers)
            if result.get("suicide_flag"):
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

    primary_severity = calculate_primary_severity(per_test, red_flags)

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
