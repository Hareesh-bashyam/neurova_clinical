import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"
USERNAME = "admin"
PASSWORD = "Hareesh"

def fail(step, resp):
    print(f"\n❌ {step} FAILED")
    print("Status:", resp.status_code)
    print(resp.text)
    sys.exit(1)

def ok(step, msg="OK"):
    print(f"✅ {step}: {msg}")

# ---------------------------
# 1️⃣ AUTH
# ---------------------------
r = requests.post(
    f"{BASE_URL}/api/v1/auth/token/",
    json={"username": USERNAME, "password": PASSWORD},
)
if r.status_code != 200:
    fail("auth", r)

token = r.json()["access"]
headers = {"Authorization": f"Bearer {token}"}
ok("auth")

# ---------------------------
# 2️⃣ CREATE PATIENT
# ---------------------------
r = requests.post(
    f"{BASE_URL}/api/v1/patients/",
    headers=headers,
    json={"name": "RAW STORAGE TEST PATIENT"},
)
if r.status_code not in (200, 201):
    fail("create patient", r)

patient_id = r.json()["id"]
ok("create patient", patient_id)

# ---------------------------
# 3️⃣ FETCH PANEL
# ---------------------------
r = requests.get(f"{BASE_URL}/api/v1/panels/", headers=headers)
if r.status_code != 200:
    fail("fetch panels", r)

panel_code = r.json()[0]["code"]
ok("fetch panel", panel_code)

# ---------------------------
# 4️⃣ CREATE ORDER
# ---------------------------
r = requests.post(
    f"{BASE_URL}/api/v1/orders/",
    headers=headers,
    json={"patient_id": patient_id, "panel_code": panel_code},
)
if r.status_code not in (200, 201):
    fail("create order", r)

order_id = r.json()["order_id"]
ok("create order", order_id)

# ---------------------------
# 5️⃣ START SESSION
# ---------------------------
r = requests.post(
    f"{BASE_URL}/api/v1/orders/{order_id}/start-session/",
    headers=headers,
)
if r.status_code not in (200, 201):
    fail("start session", r)

session_id = r.json()["session_id"]
ok("start session", session_id)

# ---------------------------
# 6️⃣ SUBMIT PHQ-9 RAW RESPONSES
# ---------------------------
responses = [3,3,3,3,3,3,3,3,1]

for idx, val in enumerate(responses, start=1):
    r = requests.post(
        f"{BASE_URL}/api/v1/sessions/{session_id}/events/",
        headers=headers,
        json={
            "event_type": "response_submitted",
            "payload": {
                "question_code": f"PHQ9_Q{idx}",
                "value": val
            }
        }
    )
    if r.status_code not in (200, 201):
        fail(f"submit response Q{idx}", r)

ok("submit raw responses")

# ---------------------------
# 7️⃣ SUBMIT CONSENT
# ---------------------------
r = requests.post(
    f"{BASE_URL}/api/v1/sessions/{session_id}/consent/",
    headers=headers,
    json={"accepted": True},
)
if r.status_code not in (200, 201):
    fail("submit consent", r)

ok("submit consent")

# ---------------------------
# 8️⃣ SCORE SESSION
# ---------------------------
r = requests.post(
    f"{BASE_URL}/api/v1/sessions/{session_id}/score/",
    headers=headers,
)
if r.status_code != 200:
    fail("score session", r)

ok("score session")

# ---------------------------
# 9️⃣ VERIFY RAW STORAGE (DB LEVEL)
# ---------------------------
from django.conf import settings
import django
django.setup()

from scoring.models import Score

score = Score.objects.latest("id")

print("\n📦 STORED SCORE RESULT:")
print(json.dumps(score.raw_result, indent=2))

# ---------------------------
# 🔒 ASSERTIONS (HARD FAIL)
# ---------------------------
assert score.raw_result["test_code"] == "PHQ9"
assert score.raw_result["test_version"] == "1.0"
assert score.raw_result["raw_responses"] == responses
assert score.raw_result["computed_score"] == 25
assert score.raw_result["severity"] == "Severe"
assert "SUICIDE_RISK" in score.raw_result["red_flags"]

print("\n🎉 ADDENDUM B VERIFIED — RAW RESPONSES IMMUTABLE")
