import os
import django
from django.conf import settings
from dotenv import load_dotenv

# LOAD ENV FIRST
load_dotenv()

# SETUP DJANGO
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "neurova_backend.settings")
django.setup()

from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from common.crypto_utils import encrypt_data, decrypt_data, ENCRYPTION_KEY
import json
import hashlib
import time

User = get_user_model()

print(f"DEBUG: Encryption Key Hash: {hashlib.sha256(ENCRYPTION_KEY).hexdigest()[:8]}")

# 1. Setup Client
client = APIClient()

# 2. Authenticate
user = User.objects.filter(is_active=True).first()
if not user:
    print("No active user found. Cannot proceed.")
    exit(1)

client.force_authenticate(user=user)
org_id = str(user.profile.organization.external_id)
print(f"Authenticated as: {user.username}")
print(f"Organization ID: {org_id}")

def print_response(step_name, data):
    print(f"\n--- {step_name} RESPONSE ---")
    print(json.dumps(data, indent=2, default=str))
    print("--------------------------------\n")

# ==========================================
# STEP 2.5: ENSURE BATTERY EXISTS
# ==========================================
print("\n[STEP 2.5] Checking/Creating Battery Data...")
from apps.clinical_ops.battery_assessment_model import Battery, Assessment, BatteryAssessment

battery_code = "MENTAL_HEALTH_CORE_V1"
test_code = "PHQ9"

# 1. Create Assessment (PHQ9)
assessment, _ = Assessment.objects.get_or_create(
    test_code=test_code,
    defaults={
        "title": "Patient Health Questionnaire-9",
        "version": "1.0",
        "questions_json": {
            "questions": [
                {"id": "PHQ9_1", "text": "Little interest or pleasure in doing things?"},
                {"id": "PHQ9_2", "text": "Feeling down, depressed, or hopeless?"}
            ]
        },
        "is_active": True
    }
)

# 2. Create Battery
battery, created = Battery.objects.get_or_create(
    battery_code=battery_code,
    defaults={
        "name": "Mental Health Core",
        "version": "1.0",
        "screening_label": "Standard Screening",
        "is_active": True
    }
)

# 3. Link them
if not battery.battery_tests.filter(assessment=assessment).exists():
    BatteryAssessment.objects.create(
        battery=battery,
        assessment=assessment,
        display_order=1
    )
    print(f"Linked {test_code} to {battery_code}")

print(f"Battery {battery_code} ready.")


# ==========================================
# STEP 3: CREATE PATIENT
# ==========================================
print("\n[STEP 3] Creating Patient...")
patient_payload = {
    "org_id": org_id,
    "full_name": "E2E Test Patient",
    "age": 45,
    "sex": "FEMALE",
    "phone": "5550199999",
    "email": "e2e_test@neurova.com"
}
enc_patient = encrypt_data(patient_payload)
resp = client.post("/api/v1/clinical-ops/staff/patients/create", {"encrypted_data": enc_patient}, format="json")

if resp.status_code != 201:
    print(f"Failed to Create Patient: {resp.status_code}")
    print(resp.content)
    exit(1)

dec_resp = decrypt_data(resp.data["encrypted_data"]) if "encrypted_data" in resp.data else resp.data
print_response("CREATE PATIENT", dec_resp)
patient_id = dec_resp.get("patient_id")
print(f"SUCCESS: Patient Created (ID: {patient_id})")

# ==========================================
# STEP 4: CREATE ORDER
# ==========================================
print("\n[STEP 4] Creating Order...")
order_payload = {
    "org_id": org_id,
    "patient_id": patient_id,
    "battery_code": "MENTAL_HEALTH_CORE_V1",
    "administration_mode": "KIOSK"
}
enc_order = encrypt_data(order_payload)
resp = client.post("/api/v1/clinical-ops/staff/orders/create", {"encrypted_data": enc_order}, format="json")

if resp.status_code != 201:
    print(f"Failed to Create Order: {resp.status_code}")
    print(resp.content)
    exit(1)

dec_order_resp = decrypt_data(resp.data["encrypted_data"]) if "encrypted_data" in resp.data else resp.data
print_response("CREATE ORDER", dec_order_resp)
order_data = dec_order_resp
order_id = order_data["order_id"]
initial_token = order_data.get('public_token')
print(f"SUCCESS: Order Created (ID: {order_id})")
print(f"Token: {initial_token}")

# ==========================================
# STEP 5: CHECK QUEUE
# ==========================================
print("\n[STEP 5] Checking Clinic Queue...")
resp = client.get("/api/v1/clinical-ops/staff/queue")
if resp.status_code != 200:
    print(f"Failed to Fetch Queue: {resp.status_code}")
    exit(1)

dec_queue_resp = decrypt_data(resp.data["encrypted_data"]) if "encrypted_data" in resp.data else resp.data
# Queue can be large, just print summary or count
print(f"Queue count: {len(dec_queue_resp.get('results', []))}")

results = dec_queue_resp.get("results", [])
found_order = next((o for o in results if o["id"] == order_id), None)

if found_order:
    print_response("QUEUE ORDER ITEM", found_order)
    token_in_queue = found_order.get('public_token')
    if token_in_queue == initial_token:
        print("SUCCESS: Order found in queue with matching token.")
    else:
        print(f"WARNING: Token mismatch! Queue: {token_in_queue}, Create: {initial_token}")
else:
    print("FAILURE: Order not found in queue!")
    exit(1)

# ==========================================
# STEP 6: PUBLIC BOOTSTRAP
# ==========================================
print("\n[STEP 6] Public Bootstrap...")
current_token = initial_token

# Public API Client (No Auth)
public_client = APIClient() 

resp = public_client.get(f"/api/v1/clinical-ops/public/order/{current_token}")
if resp.status_code != 200:
    print(f"Failed Public Bootstrap: {resp.status_code}")
    print(resp.content)
    exit(1)

dec_boot_resp = decrypt_data(resp.data["encrypted_data"]) if "encrypted_data" in resp.data else resp.data
print_response("PUBLIC BOOTSTRAP", dec_boot_resp)

new_token = dec_boot_resp.get("public_token")
print(f"SUCCESS: Bootstrap Complete. Token Rotated: {current_token[:8]}... -> {new_token[:8]}...")
current_token = new_token

# ==========================================
# STEP 7: GET CONSENT
# ==========================================
print("\n[STEP 7] Public Get Consent...")
resp = public_client.get(f"/api/v1/clinical-ops/public/order/{current_token}/consent")
if resp.status_code != 200:
    print(f"Failed Get Consent: {resp.status_code}")
    exit(1)

dec_consent_resp = decrypt_data(resp.data["encrypted_data"]) if "encrypted_data" in resp.data else resp.data
print_response("GET CONSENT", dec_consent_resp)

new_token = dec_consent_resp.get("public_token")
print(f"SUCCESS: Consent Text Retrieved. Token Rotated.")
current_token = new_token

# ==========================================
# STEP 8: SUBMIT CONSENT
# ==========================================
print("\n[STEP 8] Public Submit Consent...")
consent_payload = {
    "consent_version": "V1",
    "consent_given_by": "SELF",
    "allow_patient_copy": True,
    "consent_language": "en"
}
enc_consent_sub = encrypt_data(consent_payload)
resp = public_client.post(f"/api/v1/clinical-ops/public/order/{current_token}/consent/submit", {"encrypted_data": enc_consent_sub}, format="json")

if resp.status_code != 200:
    print(f"Failed Submit Consent: {resp.status_code}")
    print(resp.content)
    exit(1)

dec_sub_resp = decrypt_data(resp.data["encrypted_data"]) if "encrypted_data" in resp.data else resp.data
print_response("SUBMIT CONSENT", dec_sub_resp)

new_token = dec_sub_resp.get("public_token")
print(f"SUCCESS: Consent Submitted.")
current_token = new_token

# ==========================================
# STEP 9: GET QUESTIONS
# ==========================================
print("\n[STEP 9] Public Get Questions...")
resp = public_client.get(f"/api/v1/clinical-ops/public/order/{current_token}/questions")
if resp.status_code != 200:
    print(f"Failed Get Questions: {resp.status_code}")
    exit(1)

dec_q_resp = decrypt_data(resp.data["encrypted_data"]) if "encrypted_data" in resp.data else resp.data
# Truncate questions for cleaner output
debug_q_resp = dec_q_resp.copy()
debug_q_resp['tests'] = f"[{len(debug_q_resp.get('tests', []))} tests]"
print_response("GET QUESTIONS", debug_q_resp)

new_token = dec_q_resp.get("battery", {}).get("public_token") 
if not new_token:
    new_token = dec_q_resp.get("public_token")
    if not new_token: 
         new_token = dec_q_resp.get("battery", {}).get("public_token")

print(f"SUCCESS: Questions Retrieved.")
current_token = new_token

# ==========================================
# STEP 10: SUBMIT ANSWERS
# ==========================================
print("\n[STEP 10] Public Submit Answers...")
# Mock answers
answers = [{"test_code": "PHQ9", "item": "PHQ9_1", "value": 1}] * 5 # Just a dummy list
submit_payload = {
    "answers": answers,
    "duration_seconds": 120
}
enc_submit = encrypt_data(submit_payload)
resp = public_client.post(f"/api/v1/clinical-ops/public/order/{current_token}/submit", {"encrypted_data": enc_submit}, format="json")

if resp.status_code != 200:
    print(f"Failed Submit Answers: {resp.status_code}")
    print(resp.content)
    exit(1)

dec_res_resp = decrypt_data(resp.data["encrypted_data"]) if "encrypted_data" in resp.data else resp.data
print_response("SUBMIT ASSESSMENT", dec_res_resp)
print(f"SUCCESS: Assessment Submitted. Order should be COMPLETED.")

# ==========================================
# STEP 11: STAFF INBOX
# ==========================================
print("\n[STEP 11] Staff Inbox Check...")
resp = client.get("/api/v1/clinical-ops/staff/inbox")
if resp.status_code != 200:
    print(f"Failed Inbox: {resp.status_code}")
    exit(1)

dec_inbox = decrypt_data(resp.data["encrypted_data"]) if "encrypted_data" in resp.data else resp.data
results = dec_inbox.get("results", [])
found_completed = next((o for o in results if o["order_id"] == order_id), None)
if found_completed:
    print_response("INBOX ITEM", found_completed)
    print(f"SUCCESS: Order {order_id} found in Inbox (COMPLETED).")
else:
    print(f"FAILURE: Order {order_id} not found in Inbox!")
    
# ==========================================
# STEP 12: STAFF REVIEW
# ==========================================
print("\n[STEP 12] Staff Review...")
resp = client.get(f"/api/v1/clinical-ops/staff/order/{order_id}/review")
if resp.status_code != 200:
    print(f"Failed Review: {resp.status_code}")
    exit(1)

dec_review = decrypt_data(resp.data["encrypted_data"]) if "encrypted_data" in resp.data else resp.data
print_response("REVIEW DETAILS", dec_review)
print("SUCCESS: Review Details Retrieved.")

# ==========================================
# STEP 13: STAFF UPDATE STATUS (ACCEPT)
# ==========================================
print("\n[STEP 13] Staff Accept Order...")
accept_payload = {
    "action": "ACCEPT",
    "notes": "E2E Verified"
}
enc_accept = encrypt_data(accept_payload)
resp = client.post(f"/api/v1/clinical-ops/staff/order/{order_id}/accept-reject", {"encrypted_data": enc_accept}, format="json")
if resp.status_code != 200:
    print(f"Failed Accept: {resp.status_code}")
    print(resp.content)
    exit(1)

dec_accept = decrypt_data(resp.data["encrypted_data"]) if "encrypted_data" in resp.data else resp.data
print_response("ACCEPT ORDER", dec_accept)
print("SUCCESS: Order Accepted.")

# ==========================================
# STEP 14: GENERATE REPORT
# ==========================================
print("\n[STEP 14] Generate Report...")
report_payload = {
    "org_id": org_id,
    "order_id": order_id
}
enc_report = encrypt_data(report_payload)
resp = client.post("/api/v1/clinical-ops/staff/reports/generate", {"encrypted_data": enc_report}, format="json")
if resp.status_code != 200:
    print(f"Failed Generate Report: {resp.status_code}")
    print(resp.content)
    exit(1)
dec_rep_resp = decrypt_data(resp.data["encrypted_data"]) if "encrypted_data" in resp.data else resp.data
print_response("GENERATE REPORT", dec_rep_resp)
pdf_url = dec_rep_resp.get("pdf_url")
print(f"SUCCESS: Report Generated. URL: {pdf_url}")

# ==========================================
# STEP 15: DELETE ORDER
# ==========================================
print("\n[STEP 15] Delete Order...")
resp = client.delete(f"/api/v1/clinical-ops/staff/order/{order_id}/delete")
if resp.status_code != 200:
    print(f"Failed Delete: {resp.status_code}")
    exit(1)

dec_del = decrypt_data(resp.data["encrypted_data"]) if "encrypted_data" in resp.data else resp.data
print_response("DELETE ORDER", dec_del)
print("SUCCESS: Order Deleted.")

# ==========================================
# STEP 16: VERIFY DELETION IN INBOX
# ==========================================
print("\n[STEP 16] Verify Deletion (Inbox)...")
resp = client.get("/api/v1/clinical-ops/staff/inbox")
dec_inbox = decrypt_data(resp.data["encrypted_data"]) if "encrypted_data" in resp.data else resp.data
results = dec_inbox.get("results", [])
found_deleted = next((o for o in results if o["order_id"] == order_id), None)
if not found_deleted:
    print("SUCCESS: Order is gone from inbox.")
else:
    print("FAILURE: Order still present in inbox!")

print("\n\n==================================================")
print("       E2E VERIFICATION COMPLETED SUCCESSFULLY       ")
print("==================================================")
