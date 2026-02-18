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

# 3. Create Patient (Encrypted Payload)
patient_payload = {
    "org_id": org_id,
    "full_name": "Test Patient Verify",
    "age": 30,
    "sex": "MALE",
    "phone": "9999999999",
    "email": "test@verify.com"
}
enc_patient = encrypt_data(patient_payload)
print(f"Sending Encrypted Create Patient Request...")
# Use relative path for APIClient
resp = client.post("/api/v1/clinical-ops/staff/patients/create", {"encrypted_data": enc_patient}, format="json")

if resp.status_code != 201:
    print(f"Failed to Create Patient: {resp.status_code}")
    print(resp.content)
    # Check if we got a 200/400 with encrypted response?
    # Actually, failure response might be encrypted if @encrypt_response catches it? No, usually handled by view logic.
    # Let's hope for 201.
    exit(1)

dec_resp = decrypt_data(resp.data["encrypted_data"]) if "encrypted_data" in resp.data else resp.data
print("Create Patient Response (Decrypted):", dec_resp)
# Direct access because decrypt_data returns the inner data object
patient_id = dec_resp.get("patient_id")

# 4. Create Order (Encrypted Payload)
order_payload = {
    "org_id": org_id,
    "patient_id": patient_id,
    "battery_code": "MENTAL_HEALTH_CORE_V1",
    "administration_mode": "KIOSK"
}
enc_order = encrypt_data(order_payload)
print(f"Sending Encrypted Create Order Request...")
resp = client.post("/api/v1/clinical-ops/staff/orders/create", {"encrypted_data": enc_order}, format="json")

if resp.status_code != 201:
    print(f"Failed to Create Order: {resp.status_code}")
    print(resp.content)
    exit(1)

dec_order_resp = decrypt_data(resp.data["encrypted_data"]) if "encrypted_data" in resp.data else resp.data
print("Create Order Response (Decrypted):", dec_order_resp)
order_data = dec_order_resp
print(f"NEW Valid Public Token from CreateOrder: {order_data.get('public_token')}")

# 5. Check Queue (Encrypted Response)
print(f"Fetching Clinic Queue...")
resp = client.get("/api/v1/clinical-ops/staff/queue")
if resp.status_code != 200:
    print(f"Failed to Fetch Queue: {resp.status_code}")
    exit(1)

dec_queue_resp = decrypt_data(resp.data["encrypted_data"]) if "encrypted_data" in resp.data else resp.data
# Check "results"
results = dec_queue_resp.get("results", [])
print(f"Found {len(results)} orders in queue.")

# Find our new order
found_order = next((o for o in results if o["id"] == order_data["order_id"]), None)

if found_order:
    print("\n---------- VERIFICATION RESULT ----------")
    print(f"Order ID: {found_order['id']}")
    print(f"Patient Acceptance Status: {found_order.get('status')}") # Or acceptance status if exposed
    print(f"Public Token in Queue: {found_order.get('public_token')}")
    
    if found_order.get("public_token"):
        print("SUCCESS: public_token is present!")
    else:
        print("FAILURE: public_token is MISSING/None!")
else:
    print("FAILURE: Could not find the newly created order in the queue list!")

