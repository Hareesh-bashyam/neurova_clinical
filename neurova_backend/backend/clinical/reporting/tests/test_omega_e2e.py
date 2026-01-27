import uuid
import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from core.models import Organization, UserProfile
from reports.models import ClinicalReport

User = get_user_model()


@pytest.mark.django_db
def test_omega_e2e_cmha_pdf_contains_safety_and_no_leaks():
    c = APIClient()

    # -----------------------------
    # Organization
    # -----------------------------
    org = Organization.objects.create(
        name="Org",
        address="Addr",
        code="ORG_001",
        org_type="HOSPITAL",
        signature_required=True,
    )

    # -----------------------------
    # Clinician (AUTH REQUIRED)
    # -----------------------------
    clinician = User.objects.create_user(
        username="hareesh",
        password="Hareesh",
    )

    UserProfile.objects.create(
        user=clinician,
        organization=org,
        role="CLINICIAN",
    )

    c.force_authenticate(user=clinician)

    # -----------------------------
    # Create order
    # -----------------------------
    resp = c.post(
        "/api/v1/clinical/orders/",
        data={
            "organization_id": str(org.external_id),
            "patient_name": "Patient",
            "patient_age": 30,
            "patient_gender": "Male",
            "encounter_type": "OPD",
            "administration_mode": "IN_CLINIC",
            "battery_code": "CMHA_V1",
        },
        content_type="application/json",
        **{"HTTP_X_ORG_ID": str(org.external_id)},
    )

    assert resp.status_code in (200, 201)
    session_id = resp.json()["data"]["session_id"]
    order_id = resp.json()["data"]["order_id"]

    # -----------------------------
    # Start session
    # -----------------------------
    start = c.post(
        f"/api/v1/clinical/sessions/{session_id}/start/",
        content_type="application/json",
        **{"HTTP_X_ORG_ID": str(org.external_id)},
    )
    assert start.status_code == 200

    # -----------------------------
    # PHQ9 (Q9 > 0 → suicide flag)
    # -----------------------------
    c.post(
        f"/api/v1/clinical/sessions/{session_id}/submit_current/",
        data={
            "test_code": "PHQ9",
            "raw_responses": [0, 0, 0, 0, 0, 0, 0, 0, 1],
        },
        content_type="application/json",
        **{"HTTP_X_ORG_ID": str(org.external_id)},
    )

    # -----------------------------
    # MDQ
    # -----------------------------
    c.post(
        f"/api/v1/clinical/sessions/{session_id}/submit_current/",
        data={
            "test_code": "MDQ",
            "raw_responses": {
                "symptom_yes_count": 7,
                "co_occur": True,
                "impairment": "MODERATE",
            },
        },
        content_type="application/json",
        **{"HTTP_X_ORG_ID": str(org.external_id)},
    )

    # -----------------------------
    # GAD7
    # -----------------------------
    c.post(
        f"/api/v1/clinical/sessions/{session_id}/submit_current/",
        data={
            "test_code": "GAD7",
            "raw_responses": [0, 0, 0, 0, 0, 0, 0],
        },
        content_type="application/json",
        **{"HTTP_X_ORG_ID": str(org.external_id)},
    )

    # -----------------------------
    # PSS10
    # -----------------------------
    c.post(
        f"/api/v1/clinical/sessions/{session_id}/submit_current/",
        data={
            "test_code": "PSS10",
            "raw_responses": [0] * 10,
        },
        content_type="application/json",
        **{"HTTP_X_ORG_ID": str(org.external_id)},
    )

    # -----------------------------
    # AUDIT
    # -----------------------------
    c.post(
        f"/api/v1/clinical/sessions/{session_id}/submit_current/",
        data={
            "test_code": "AUDIT",
            "raw_responses": [0] * 10,
        },
        content_type="application/json",
        **{"HTTP_X_ORG_ID": str(org.external_id)},
    )

    # -----------------------------
    # STOP_BANG
    # -----------------------------
    c.post(
        f"/api/v1/clinical/sessions/{session_id}/submit_current/",
        data={
            "test_code": "STOP_BANG",
            "raw_responses": [0] * 8,
        },
        content_type="application/json",
        **{"HTTP_X_ORG_ID": str(org.external_id)},
    )

    # -----------------------------
    # Generate report
    # -----------------------------
    rep_resp = c.post(
        f"/api/v1/clinical/orders/{order_id}/generate_report/",
        content_type="application/json",
        **{"HTTP_X_ORG_ID": str(org.external_id)},
    )
    assert rep_resp.status_code == 200, rep_resp.json()

    # -----------------------------
    # Mark Reviewed (MANDATORY for safety flags)
    # -----------------------------
    report = ClinicalReport.objects.get(order_id=order_id)

    review = c.post(
        f"/api/v1/reports/{report.id}/mark-reviewed/",
        content_type="application/json",
        **{"HTTP_X_ORG_ID": str(org.external_id)},
    )
    assert review.status_code == 200

    # -----------------------------
    # Fetch PDF
    # -----------------------------
    pdf = c.get(
        f"/api/v1/clinical/orders/{order_id}/report/pdf/",
        **{"HTTP_X_ORG_ID": str(org.external_id)},
    )
    assert pdf.status_code == 200

    text = pdf.content.decode("latin-1", errors="ignore")

    # -----------------------------
    # Assertions
    # -----------------------------
    assert "Psychiatric Assessment Report" in text
    assert "Important Safety Information" in text

    assert "Patient Name: Patient" in text
    assert "Age / Gender: 30 / Male" in text

    forbidden = [
        "Engine Version",
        "Schema Version",
        "Session ID",
        "Org Name",
    ]

    for f in forbidden:
        assert f not in text
