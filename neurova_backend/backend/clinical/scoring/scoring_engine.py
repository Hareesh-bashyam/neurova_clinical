"""
Clinical Scoring Engine — V1
Uses existing validated scoring logic.
"""

# ---------- helpers ----------

def calculate_sum(responses):
    return sum(responses)

def calculate_reverse_sum(responses, reverse_items):
    total = 0
    for i, val in enumerate(responses, start=1):
        if i in reverse_items:
            total += 4 - val
        else:
            total += val
    return total

def apply_severity(score, severity_map):
    for low, high, label in severity_map:
        if low <= score <= high:
            return label
    return None


# ---------- instrument evaluators ----------

def evaluate_phq9(responses):
    score = calculate_sum(responses)
    suicide_flag = responses[8] > 0 if len(responses) >= 9 else False
    return score, suicide_flag

def evaluate_mdq(symptom_yes_count, co_occur, impairment):
    if symptom_yes_count >= 7 and co_occur and impairment in ["MODERATE", "SEVERE"]:
        return "POSITIVE"
    return "NEGATIVE"

def evaluate_asrs(part_a_positive_count):
    return "POSITIVE" if part_a_positive_count >= 4 else "NEGATIVE"


# ---------- REQUIRED ENTRY POINT ----------
# Clinical Ops calls ONLY this function

def score_battery(battery_code: str, battery_version: str, answers_json: dict) -> dict:
    """
    REQUIRED ENTRY POINT — DO NOT RENAME

    answers_json format:
    {
        "answers": [{"question_id": "...", "value": int}, ...],
        "meta": {...}
    }
    """

    answers = answers_json.get("answers", [])
    values = [a.get("value", 0) for a in answers if isinstance(a.get("value"), int)]

    result = {
        "battery_code": battery_code,
        "battery_version": battery_version,
        "summary": {},
        "per_test": {},
        "flags": [],
    }

    # ---- PHQ-9 ----
    if battery_code == "MENTAL_HEALTH_CORE_V1" and len(values) >= 9:
        score, suicide_flag = evaluate_phq9(values[:9])

        severity = apply_severity(
            score,
            [
                (0, 4, "MINIMAL"),
                (5, 9, "MILD"),
                (10, 14, "MODERATE"),
                (15, 19, "MODERATELY_SEVERE"),
                (20, 27, "SEVERE"),
            ]
        )

        result["per_test"]["PHQ9"] = {
            "score": score,
            "severity": severity,
            "suicide_flag": suicide_flag,
        }

        result["summary"] = {
            "primary_severity": severity,
            "has_red_flags": suicide_flag,
        }

        if suicide_flag:
            result["flags"].append("SUICIDE_RISK")

    else:
        # fallback for unsupported batteries
        result["summary"] = {
            "primary_severity": "UNKNOWN",
            "has_red_flags": False,
        }

    return result
