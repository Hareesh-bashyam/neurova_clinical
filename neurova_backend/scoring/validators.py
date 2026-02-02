VALID_RANGES = { 
    "PHQ9": (0, 3), 
    "GAD7": (0, 3), 
    "PSS10": (0, 4), 
} 
 
def validate_answers(test_code, answers): 
    min_v, max_v = VALID_RANGES[test_code] 
    for a in answers: 
        if not (min_v <= a <= max_v): 
            raise ValidationError(f"Invalid {test_code} value: {a}")