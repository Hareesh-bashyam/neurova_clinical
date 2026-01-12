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

def evaluate_phq9(responses):
    score = calculate_sum(responses)
    suicide_flag = responses[8] > 0
    return score, suicide_flag

def evaluate_mdq(symptom_yes_count, co_occur, impairment):
    if symptom_yes_count >= 7 and co_occur and impairment in ["MODERATE","SEVERE"]:
        return "POSITIVE"
    return "NEGATIVE"

def evaluate_asrs(part_a_positive_count):
    return "POSITIVE" if part_a_positive_count >= 4 else "NEGATIVE"
