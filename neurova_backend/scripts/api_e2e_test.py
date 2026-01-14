import requests
import sys

BASE_URL = "http://127.0.0.1:8000"
USERNAME = "hareesh"
PASSWORD = "Hareesh"


def fail(step, resp):
    print(f"\n[FAIL] {step}")
    print("Status:", resp.status_code)
    try:
        print(repr(resp.text[:100000]))
    except Exception:
        print("(Could not print text)")
    sys.exit(1)


def ok(step, msg="OK"):
    print(f"[OK] {step}: {msg}")


# 1. AUTH
r = requests.post(
    f"{BASE_URL}/api/v1/auth/token/",
    json={"username": USERNAME, "password": PASSWORD},
)
if r.status_code != 200:
    fail("auth", r)

token = r.json()["access"]
headers = {"Authorization": f"Bearer {token}"}
ok("auth")


# 2. IMPORT CATALOG
r = requests.post(
    f"{BASE_URL}/api/v1/catalog/import/",
    headers=headers,
    json={
        "instruments": [
            {"code": "PHQ9", "version": "v1.0", "name": "PHQ-9", "license_type": "Public Domain"}
        ],
        "tests": [
            {
                "instrument": "PHQ9",
                "instrument_version": "v1.0",
                "code": "PHQ9_STD",
                "version": "v1.0",
                "name": "PHQ-9 Standard",
                "json_schema": {
                    "type": "object",
                    "properties": {f"q{i}": {"type": "integer"} for i in range(1, 10)},
                },
                "scoring_spec": {
                    "severity_thresholds": [
                        {"max": 4, "label": "Minimal"},
                        {"max": 9, "label": "Mild"},
                        {"max": 14, "label": "Moderate"},
                        {"max": 19, "label": "Moderately Severe"},
                        {"max": 999, "label": "Severe"},
                    ]
                },
            }
        ],
        "panels": [
            {"code": "MENTAL_HEALTH_BASIC", "name": "Mental Health Panel", "tests": ["PHQ9_STD"]}
        ],
    },
)
if r.status_code != 200:
    fail("catalog import", r)
ok("catalog import")


# 3. CREATE PATIENT
r = requests.post(
    f"{BASE_URL}/api/v1/patients/",
    headers=headers,
    json={"name": "B11 Smoke Patient"},
)
if r.status_code not in (200, 201):
    fail("create patient", r)

patient_id = r.json()["id"]
ok("create patient", patient_id)


# 4. FETCH PANELS
r = requests.get(f"{BASE_URL}/api/v1/panels/", headers=headers)
panel_code = r.json()[0]["code"]
ok("fetch panels", panel_code)


# 5. CREATE ORDER
r = requests.post(
    f"{BASE_URL}/api/v1/orders/",
    headers=headers,
    json={"patient_id": patient_id, "panel_code": panel_code},
)
order_id = r.json()["order_id"]
ok("create order", order_id)


# 6. START SESSION
r = requests.post(
    f"{BASE_URL}/api/v1/orders/{order_id}/start-session/",
    headers=headers,
)
session_id = r.json()["session_id"]
ok("start session", session_id)


# 7. SUBMIT RESPONSES
r = requests.post(
    f"{BASE_URL}/api/v1/sessions/{session_id}/events/",
    headers=headers,
    json={
        "event_type": "responses_submitted",
        "responses": {
            "q1": 3, "q2": 3, "q3": 3,
            "q4": 3, "q5": 3, "q6": 3,
            "q7": 3, "q8": 3, "q9": 1,
        },
    },
)
if r.status_code != 200:
    fail("submit responses", r)
ok("submit responses")


# 8. SUBMIT CONSENT
r = requests.post(
    f"{BASE_URL}/api/v1/sessions/{session_id}/consent/",
    headers=headers,
    json={"consent_given": True, "source": "patient_app"},
)
if r.status_code != 200:
    fail("submit consent", r)
ok("submit consent")


# 9. SCORE SESSION (answers must be provided for now)
r = requests.post(
    f"{BASE_URL}/api/v1/sessions/{session_id}/score/",
    headers=headers,
    json={
        "answers": {
            "q1": 3, "q2": 3, "q3": 3,
            "q4": 3, "q5": 3, "q6": 3,
            "q7": 3, "q8": 3, "q9": 1,
        }
    },
)
if r.status_code != 200:
    fail("score session", r)
ok("score session")


# 10. GENERATE REPORT
r = requests.post(
    f"{BASE_URL}/api/v1/sessions/{session_id}/report/",
    headers=headers,
)
if r.status_code not in (200, 201):
    fail("generate report", r)

data = r.json()
report_id = data.get("report_id") or data.get("id")
ok("generate report", report_id)


# 11. SIGN REPORT
r = requests.post(
    f"{BASE_URL}/api/v1/reports/{report_id}/sign/",
    headers=headers,
    json={
        "signer_name": "Dr Rao",
        "signer_reg_no": "APMC-44321",
        "signer_role": "Psychiatrist",
    },
)
if r.status_code != 200:
    fail("sign report", r)
ok("sign report")


# 12. RELEASE REPORT
r = requests.post(
    f"{BASE_URL}/api/v1/reports/{report_id}/release/",
    headers=headers,
)
if r.status_code != 200:
    fail("release report", r)
ok("release report")


# 13. FETCH PDF (FINAL ASSERTION)
r = requests.get(
    f"{BASE_URL}/api/v1/reports/{report_id}/pdf/",
    headers=headers,
)

if r.status_code != 200:
    fail("fetch pdf", r)

if not r.content.startswith(b"%PDF"):
    print("[FAIL] pdf validation: not a valid PDF")
    sys.exit(1)

pdf_path = f"report_{report_id}.pdf"
with open(pdf_path, "wb") as f:
    f.write(r.content)

ok("fetch pdf", f"saved as {pdf_path}")


print("\n[SUCCESS] B11 MANUAL SMOKE RUN - PASSED")
print("PDF + JSON + SIGNATURE + RELEASE FLOW IS 100% WIRED")
