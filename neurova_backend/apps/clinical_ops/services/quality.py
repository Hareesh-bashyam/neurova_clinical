def compute_quality(duration_seconds: int, answers: list) -> dict:
    """
    answers: list of dicts: {"question_id": "...", "value": int}
    """
    values = [a.get("value") for a in answers if isinstance(a.get("value"), int)]
    straight = False
    if len(values) >= 8:
        # if 90% same answer => straight-lining
        most = max(set(values), key=values.count)
        if values.count(most) / max(1, len(values)) >= 0.9:
            straight = True

    too_fast = duration_seconds > 0 and duration_seconds < 60  # < 60 sec entire battery
    inconsistency = False  # placeholder: add rules later if needed

    return {
        "duration_seconds": duration_seconds,
        "straight_lining_flag": straight,
        "too_fast_flag": too_fast,
        "inconsistency_flag": inconsistency,
        "notes": "Auto quality flags. Does not affect scoring. Clinician review only."
    }
