import json
from pathlib import Path
from scoring.engines.base import score_from_spec
from safety.rules import detect_flags

FIX = Path(__file__).resolve().parents[1] / "fixtures"

def _load_cases(name):
    return json.loads((FIX / name).read_text())

def test_phq9_cases_match_expected():
    # Example spec (must match catalog scoring_spec shape used in import)
    scoring_spec = {
        "severity_thresholds": [
            {"max": 4, "label": "Minimal"},
            {"max": 9, "label": "Mild"},
            {"max": 14, "label": "Moderate"},
            {"max": 19, "label": "Moderately Severe"},
            {"max": 999, "label": "Severe"}
        ]
    }
    cases = _load_cases("phq9_cases.json")
    for c in cases:
        res = score_from_spec(c["answers"], scoring_spec)
        assert res["total"] == c["expected_total"]
        assert res["severity"] == c["expected_severity"]
        flags = detect_flags("PHQ9", c["answers"])
        assert (len(flags) > 0) == c["expected_flag"]

