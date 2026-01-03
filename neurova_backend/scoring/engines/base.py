def score_from_spec(answers: dict, scoring_spec: dict) -> dict:
    """
    Generic deterministic scorer based on scoring_spec.
    scoring_spec format must be respected exactly.
    Returns: {"total": int, "severity": str, "subscales": {...}}
    """

    total = 0
    reverse = scoring_spec.get("reverse_scoring", {})

    for k, v in answers.items():
        if k in reverse:
            v = reverse[k].get(str(v), v)
        total += int(v)

    severity = "UNSPECIFIED"
    thresholds = scoring_spec.get("severity_thresholds", [])

    for t in thresholds:
        if total <= int(t["max"]):
            severity = t["label"]
            break
    else:
        if thresholds:
            severity = thresholds[-1]["label"]

    return {
        "total": total,
        "severity": severity,
        "subscales": {},
    }
