import uuid
import pytest
from django.test import Client
from backend.clinical.org.models import Organization
from backend.clinical.audit.models import ClinicalAuditEvent

@pytest.mark.django_db
def test_pdf_export_creates_at_audit_event():
    c = Client()
    org = Organization.objects.create(id=uuid.uuid4(), name="Org", address="Addr")

    # 1. Create Order
    resp = c.post("/api/v1/clinical/orders/",
                  data={
                      "organization_id": str(org.id),
                      "patient_name": "Test Patient",
                      "encounter_type": "OPD",
                      "administration_mode": "IN_CLINIC",
                      "battery_code": "CMHA_V1",
                      "patient_age": 30,
                      "patient_gender": "Male",
                  },
                  content_type="application/json",
                  **{"HTTP_X_ORG_ID": str(org.id)}
                  )
    assert resp.status_code == 201
    order_id = resp.json()["data"]["order_id"]
    session_id = resp.json()["data"]["session_id"]

    # 2. Start Session (updates order/session status)
    resp = c.post(f"/api/v1/clinical/sessions/{session_id}/start/",
           content_type="application/json",
           **{"HTTP_X_ORG_ID": str(org.id)})
    assert resp.status_code == 200
    current_test_code = resp.json()["data"]["test_code"]

    # 3. Simulate completion (Directly submitting required tests to be faster, or mocking)
    # Using the existing flow from e2e test to be safe and integration-like
    
    # PHQ9 (Test 1)
    resp = c.post(f"/api/v1/clinical/sessions/{session_id}/submit_current/",
           data={"raw_responses":[0]*9, "test_code": current_test_code}, # Last item > 0 triggers safety checks but completing is fine
           content_type="application/json",
           **{"HTTP_X_ORG_ID": str(org.id)})
    assert resp.status_code == 200
    current_test_code = resp.json()["data"].get("next_test_code")
           
    # MDQ (Test 2)
    resp = c.post(f"/api/v1/clinical/sessions/{session_id}/submit_current/",
           data={"raw_responses":{"symptom_yes_count":0,"co_occur":False,"impairment":"NONE"}, "test_code": current_test_code},
           content_type="application/json",
           **{"HTTP_X_ORG_ID": str(org.id)})
    assert resp.status_code == 200
    current_test_code = resp.json()["data"].get("next_test_code")

    # GAD7 (Test 3)
    resp = c.post(f"/api/v1/clinical/sessions/{session_id}/submit_current/",
           data={"raw_responses":[0]*7, "test_code": current_test_code},
           content_type="application/json",
           **{"HTTP_X_ORG_ID": str(org.id)})
    assert resp.status_code == 200
    current_test_code = resp.json()["data"].get("next_test_code")

    # PSS10 (Test 4)
    resp = c.post(f"/api/v1/clinical/sessions/{session_id}/submit_current/",
           data={"raw_responses":[0]*10, "test_code": current_test_code},
           content_type="application/json",
           **{"HTTP_X_ORG_ID": str(org.id)})
    assert resp.status_code == 200
    current_test_code = resp.json()["data"].get("next_test_code")
           
    # AUDIT (Test 5)
    resp = c.post(f"/api/v1/clinical/sessions/{session_id}/submit_current/",
           data={"raw_responses":[0]*10, "test_code": current_test_code},
           content_type="application/json",
           **{"HTTP_X_ORG_ID": str(org.id)})
    assert resp.status_code == 200
    current_test_code = resp.json()["data"].get("next_test_code")
           
    # STOP_BANG (Test 6)
    # This should complete the session
    resp = c.post(f"/api/v1/clinical/sessions/{session_id}/submit_current/",
           data={"raw_responses":[0]*8, "test_code": current_test_code},
           content_type="application/json",
           **{"HTTP_X_ORG_ID": str(org.id)})
    
    if resp.status_code != 200:
        print(f"STOP_BANG submit failed: {resp.status_code} {resp.content}")
    
    assert resp.status_code == 200
    assert resp.json()["data"].get("completed") is True
    
    # 4. Generate Report
    resp = c.post(f"/api/v1/clinical/orders/{order_id}/generate_report/", 
                  content_type="application/json", 
                  **{"HTTP_X_ORG_ID": str(org.id)})
    assert resp.status_code == 200

    # 5. Download PDF
    pdf_resp = c.get(f"/api/v1/clinical/orders/{order_id}/report/pdf/", **{"HTTP_X_ORG_ID": str(org.id)})
    assert pdf_resp.status_code == 200
    assert pdf_resp["Content-Type"] == "application/pdf"

    # 6. Verify Audit Event
    audit_events = ClinicalAuditEvent.objects.filter(order_id=order_id, event_type="PDF_EXPORTED")
    assert audit_events.exists()
    
    event = audit_events.first()
    assert event.actor == "anonymous" # Client() is unauthenticated by default unless force_login
    assert str(event.organization_id) == str(org.id)
    assert event.report_id is not None
