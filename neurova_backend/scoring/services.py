def compute_score(answers: dict) -> dict:
    """
    Simple PHQ-9 style scoring
    """
    total = sum(int(v) for v in answers)

    if total <= 4:
        severity = "minimal"
    elif total <= 9:
        severity = "mild"
    elif total <= 14:
        severity = "moderate"
    elif total <= 19:
        severity = "moderately_severe"
    else:
        severity = "severe"

    return {
        "score": total,
        "severity": severity,
        "answers": answers,
    }
