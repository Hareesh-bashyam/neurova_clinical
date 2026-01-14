import uuid
import pytest
from django.test import Client
from backend.clinical.org.models import Organization

@pytest.mark.django_db
def test_omega_e2e_cmha_pdf_contains_safety_and_no_leaks():
    c = Client()
    org = Organization.objects.create(id=uuid.uuid4(), name="Org", address="Addr")

    # create order
    resp = c.post("/api/v1/clinical/orders/",
                  data={
                      "organization_id": str(org.id),
                      "patient_name": "Patient",
                      "patient_age": 30,
                      "patient_gender": "Male",
                      "encounter_type": "OPD",
                      "administration_mode": "IN_CLINIC",
                      "battery_code": "CMHA_V1"
                  },
                  content_type="application/json",
                  **{"HTTP_X_ORG_ID": str(org.id)}
                  )
    assert resp.status_code in (200,201)
    session_id = resp.json()["session_id"]
    order_id = resp.json()["order_id"]

    # start session
    c.post(f"/api/v1/clinical/sessions/{session_id}/start/", content_type="application/json", **{"HTTP_X_ORG_ID": str(org.id)})

    # submit PHQ9 with Q9 > 0 (last item)
    c.post(f"/api/v1/clinical/sessions/{session_id}/submit_current/",
           data={"raw_responses":[0,0,0,0,0,0,0,0,1]},
           content_type="application/json",
           **{"HTTP_X_ORG_ID": str(org.id)})

    # MDQ
    c.post(f"/api/v1/clinical/sessions/{session_id}/submit_current/",
           data={"raw_responses":{"symptom_yes_count":7,"co_occur":True,"impairment":"MODERATE"}},
           content_type="application/json",
           **{"HTTP_X_ORG_ID": str(org.id)})

    # GAD7
    c.post(f"/api/v1/clinical/sessions/{session_id}/submit_current/",
           data={"raw_responses":[0,0,0,0,0,0,0]},
           content_type="application/json",
           **{"HTTP_X_ORG_ID": str(org.id)})

    # PSS10
    c.post(f"/api/v1/clinical/sessions/{session_id}/submit_current/",
           data={"raw_responses":[0,0,0,0,0,0,0,0,0,0]},
           content_type="application/json",
           **{"HTTP_X_ORG_ID": str(org.id)})

    # AUDIT
    c.post(f"/api/v1/clinical/sessions/{session_id}/submit_current/",
           data={"raw_responses":[0]*10},
           content_type="application/json",
           **{"HTTP_X_ORG_ID": str(org.id)})

    # STOP_BANG
    c.post(f"/api/v1/clinical/sessions/{session_id}/submit_current/",
           data={"raw_responses":[0]*8},
           content_type="application/json",
           **{"HTTP_X_ORG_ID": str(org.id)})

    # generate report
    rep_resp = c.post(f"/api/v1/clinical/orders/{order_id}/generate_report/", content_type="application/json", **{"HTTP_X_ORG_ID": str(org.id)})
    assert rep_resp.status_code == 200, f"Report generation failed: {rep_resp.json()}"

    # pdf
    pdf = c.get(f"/api/v1/clinical/orders/{order_id}/report/pdf/", **{"HTTP_X_ORG_ID": str(org.id)})
    assert pdf.status_code == 200
    txt = pdf.content.decode("latin-1", errors="ignore")

    assert "Psychiatric Assessment Report" in txt
    assert "Important Safety Information" in txt
    assert "14416" in txt
    
    # Verify missing fields are now present
    assert "Patient Name: Patient" in txt
    assert "Age / Gender: 30 / Male" in txt

    forbidden = ["Engine Version", "Schema Version", "Session ID", "Org Name"]
    for f in forbidden:
        assert f not in txt

