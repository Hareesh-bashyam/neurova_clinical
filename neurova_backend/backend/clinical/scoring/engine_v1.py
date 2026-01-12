def score_phq9(raw_responses):
    total = sum(raw_responses)

    if total <= 4:
        severity = "MINIMAL"
    elif total <= 9:
        severity = "MILD"
    elif total <= 14:
        severity = "MODERATE"
    elif total <= 19:
        severity = "MODERATELY_SEVERE"
    else:
        severity = "SEVERE"

    return {
        "test_code": "PHQ9",
        "score": total,
        "severity": severity,
    }
