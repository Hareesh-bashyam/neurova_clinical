
import requests
import json
import sys
import time

BASE_URL = "http://localhost:8000/api/v1/clinical"

def log(msg):
    print(f"[TEST] {msg}")

def fail(msg):
    print(f"[FAIL] {msg}")
    sys.exit(1)

import uuid

def create_session():
    # 1. Create Order
    patient_id = "PAT_TEST_003"
    log(f"Creating order for patient {patient_id}...")
    resp = requests.post(f"{BASE_URL}/orders/", json={
        "organization_id": str(uuid.uuid4()),
        "patient_name": "Test Patient",
        "encounter_type": "INITIAL",
        "administration_mode": "IN_CLINIC",
        "battery_code": "CMHA_V1"
    })
    if resp.status_code != 201:
        fail(f"Failed to create order: {resp.text}")
    order_id = resp.json()["order_id"]
    session_id = resp.json()["session_id"]
    log(f"Order created: {order_id}")
    log(f"Session created: {session_id}")
    
    return session_id

def test_resume_consistency():
    log("\n=== 3.1 RESUME BEHAVIOR — CURRENT TEST CONSISTENCY ===")
    session_id = create_session()

    # Start Session
    log("Starting session...")
    resp = requests.post(f"{BASE_URL}/sessions/{session_id}/start/")
    if resp.status_code != 200:
        fail(f"Failed to start session: {resp.text}")

    # Verify first test is PHQ9
    test_code = resp.json()["test_code"]
    if test_code != "PHQ9":
        fail(f"Expected PHQ9, got {test_code}")
    
    # Submit PHQ9
    log("Submitting PHQ9...")
    responses = {"q1": 0, "q2": 1, "q9": 0} # Minimal dummy data
    resp = requests.post(f"{BASE_URL}/sessions/{session_id}/submit_current/", json={
        "test_code": "PHQ9",
        "raw_responses": responses
    })
    if resp.status_code != 200:
        fail(f"Failed to submit PHQ9: {resp.text}")
    
    log("Verifying next test is MDQ...")
    data = resp.json()
    if data["next_test_code"] != "MDQ":
        fail(f"Expected next test MDQ, got {data.get('next_test_code')}")

    # Call GET /current/ twice
    log("Calling GET /current/ (1st)..")
    resp1 = requests.get(f"{BASE_URL}/sessions/{session_id}/current/")
    log(f"1st Response: {resp1.json().get('test_code')}")
    
    log("Calling GET /current/ (2nd)..")
    resp2 = requests.get(f"{BASE_URL}/sessions/{session_id}/current/")
    log(f"2nd Response: {resp2.json().get('test_code')}")

    if resp1.json().get("test_code") != "MDQ":
        fail(f"1st GET /current/ expected MDQ, got {resp1.json().get('test_code')}")
    if resp2.json().get("test_code") != "MDQ":
        fail(f"2nd GET /current/ expected MDQ, got {resp2.json().get('test_code')}")
    
    log("PASS: Resume behavior consistent (Idempotency confirmed)")

def test_duplicate_submission():
    log("\n=== 3.2 DUPLICATE SUBMISSION BLOCKING ===")
    session_id = create_session()

    # Start Session
    requests.post(f"{BASE_URL}/sessions/{session_id}/start/")
    
    # Submit PHQ9 (1st time)
    log("Submitting PHQ9 (1st time)...")
    resp = requests.post(f"{BASE_URL}/sessions/{session_id}/submit_current/", json={
        "test_code": "PHQ9",
        "raw_responses": {"q1": 0}
    })
    if resp.status_code != 200:
        fail(f"Failed initial submission: {resp.text}")

    # Submit PHQ9 (2nd time) - SHOULD FAIL
    log("Submitting PHQ9 (2nd time) - EXPECTING FAILURE...")
    resp = requests.post(f"{BASE_URL}/sessions/{session_id}/submit_current/", json={
        "test_code": "PHQ9",
        "raw_responses": {"q1": 0}
    })
    
    if resp.status_code == 409:
        log("PASS: Duplicate submission rejected with 409")
    else:
        log(f"FAIL: Expected 409, got {resp.status_code}")
        print(resp.text)
        sys.exit(1)

def test_submission_integrity():
    log("\n=== SUBMISSION INTEGRITY (Wrong Test Code) ===")
    session_id = create_session()
    requests.post(f"{BASE_URL}/sessions/{session_id}/start/")

    # Current test is PHQ9. Try submitting "MDQ"
    log("Current is PHQ9. Trying to submit MDQ...")
    resp = requests.post(f"{BASE_URL}/sessions/{session_id}/submit_current/", json={
        "test_code": "MDQ",
        "raw_responses": {}
    })
    
    if resp.status_code == 409:
         log("PASS: Mismatched test code rejected with 409")
    else:
        log(f"FAIL: Expected 409 for mismatched test, got {resp.status_code}")
        print(resp.text)
        sys.exit(1)


if __name__ == "__main__":
    try:
        test_resume_consistency()
        test_duplicate_submission()
        test_submission_integrity()
        log("\nALL STEP 3 VALIDATIONS PASSED ✅")
    except Exception as e:
        fail(f"Exception during test: {e}")
