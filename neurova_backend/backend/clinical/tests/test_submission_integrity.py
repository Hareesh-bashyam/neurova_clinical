import uuid
import pytest
from django.test import Client
from backend.clinical.org.models import Organization

@pytest.mark.django_db
def test_submission_integrity_vulnerability():
    """
    Reproduction test for submission integrity vulnerability.
    VERIFIES that replayed submissions are accepted and advance the battery index incorrectly.
    """
    c = Client()
    org = Organization.objects.create(id=uuid.uuid4(), name="Org", address="Addr")

    # 1. Create order for CMHA_V1 (PHQ9 -> MDQ -> GAD7 ...)
    resp = c.post("/api/v1/clinical/orders/",
                  data={
                      "organization_id": str(org.id),
                      "patient_name": "Patient",
                      "encounter_type": "OPD",
                      "administration_mode": "IN_CLINIC",
                      "battery_code": "CMHA_V1"
                  },
                  content_type="application/json",
                  **{"HTTP_X_ORG_ID": str(org.id)}
                  )
    assert resp.status_code == 201
    session_id = resp.json()["data"]["session_id"]

    # 2. Start session
    resp = c.post(f"/api/v1/clinical/sessions/{session_id}/start/", 
           content_type="application/json", 
           **{"HTTP_X_ORG_ID": str(org.id)})
    assert resp.status_code == 200
    assert resp.json()["data"]["test_code"] == "PHQ9"

    # 3. Submit PHQ9 (Valid)
    phq9_payload = {"raw_responses": [0,0,0,0,0,0,0,0,0], "test_code": "PHQ9"}
    resp = c.post(f"/api/v1/clinical/sessions/{session_id}/submit_current/",
           data=phq9_payload,
           content_type="application/json",
           **{"HTTP_X_ORG_ID": str(org.id)})
    
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["next_test_code"] == "MDQ" 
    assert data["next_test_index"] == 1

    # 4. ATTACK: Replay PHQ9 submission
    # We send the EXACT SAME payload again.
    # The server expects MDQ, but we send PHQ9 data (array of 9 zeros).
    # MDQ expects dict, but server might not validate schema deeply enough, OR 
    # if we send generic data it might just accept it.
    # Even worse: simple replay.
    
    resp_attack = c.post(f"/api/v1/clinical/sessions/{session_id}/submit_current/",
           data=phq9_payload,  # Replaying PHQ9 data
           content_type="application/json",
           **{"HTTP_X_ORG_ID": str(org.id)})

    # CURRENT VULNERABLE BEHAVIOR:
    # Server accepts it, treating it as the submission for MDQ (Index 1).
    # Advances to GAD7 (Index 2).
    
    if resp_attack.status_code == 200:
        data_attack = resp_attack.json()
        print(f"\n[VULNERABILITY CONFIRMED] Attack succeeded. Advanced to: {data_attack.get('next_test_code')}")
        
        # If bug exists, we are now at GAD7
        if data_attack.get("next_test_code") == "GAD7":
            pytest.fail("VULNERABILITY CONFIRMED: Replayed PHQ9 submission caused skip of MDQ.")
    
    # If fixed, this should be 409 or 400
    assert resp_attack.status_code in (400, 409), f"Should recognize mismatch/replay. Got {resp_attack.status_code}"
