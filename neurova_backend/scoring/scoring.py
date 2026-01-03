PHQ9_SEVERITY = [
    (0, 4, "minimal"),
    (5, 9, "mild"),
    (10, 14, "moderate"),
    (15, 19, "moderately_severe"),
    (20, 27, "severe"),
]


def score_phq9(answers: dict):
    total = sum(answers.values())

    for low, high, label in PHQ9_SEVERITY:
        if low <= total <= high:
            return total, label

    return total, "unknown"
