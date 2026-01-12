from scoring_engine import (
    calculate_sum,
    calculate_reverse_sum,
    apply_severity,
    evaluate_phq9
)
import json
from pathlib import Path

BASE = Path(__file__).parent

severity_maps = json.loads((BASE / "severity_maps.json").read_text())

# ---------- PHQ9 TEST ----------
phq9_responses = [3,3,3,3,3,3,3,3,1]

score, suicide_flag = evaluate_phq9(phq9_responses)
severity = apply_severity(score, severity_maps["PHQ9"])

print("PHQ9 SCORE:", score)
print("PHQ9 SEVERITY:", severity)
print("PHQ9 SUICIDE FLAG:", suicide_flag)

# ---------- GAD7 TEST ----------
gad7_responses = [2,2,2,2,2,2,2]

gad7_score = calculate_sum(gad7_responses)
gad7_severity = apply_severity(gad7_score, severity_maps["GAD7"])

print("GAD7 SCORE:", gad7_score)
print("GAD7 SEVERITY:", gad7_severity)
