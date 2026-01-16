"""
This adapter makes Clinical Ops independent.

RULE:
- If your scoring engine already exists elsewhere, import it here.
- If not, you MUST create the function score_battery() in the exact location mentioned below.
"""

def score_battery(battery_code: str, battery_version: str, answers_json: dict) -> dict:
    """
    Must return a JSON dict containing:
    - per_test scores
    - severity bands
    - red flag indicators
    - a top-level summary
    """
    try:
        # ✅ If your real engine exists, KEEP this import and implement there.
        from backend.clinical.scoring.scoring_engine import score_battery as real_score_battery
        return real_score_battery(
            battery_code=battery_code,
            battery_version=battery_version,
            answers_json=answers_json
        )
    except Exception as e:
        # DO NOT silently pass. Fail loudly so we fix properly.
        raise RuntimeError(
            "Scoring engine missing. Create: apps/clinical_engine/services/scoring.py "
            "with function score_battery(battery_code, battery_version, answers_json). "
            f"Original error: {str(e)}"
        )
