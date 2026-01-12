import pytest

from django.contrib.auth.models import User
from rest_framework.test import APIClient

from core.models import Organization, UserProfile
from catalog.models import Instrument, TestDefinition, Panel
from patients.models import Patient
from orders.models import Order
from sessions.models import Session
from reports.models import Report, ReportSignature


@pytest.mark.django_db
def test_report_release_logic():
    """
    B4 — REPORT RELEASE LOGIC

    Rules:
    - STAFF cannot release
    - CLINICIAN requires signature
    - Release does NOT mutate report (immutable)
    """

    client = APIClient()

    # --------------------------------------------------
    # Base setup
    # --------------------------------------------------
    org = Organization.objects.create(
        name="Test Clinic",
        signature_required=True
    )

    clinician = User.objects.create_user(
        username="clinician@test.com",
        password="pass123"
    )
    UserProfile.objects.create(
        user=clinician,
        organization=org,
        role="CLINICIAN"
    )

    staff = User.objects.create_user(
        username="staff@test.com",
        password="pass123"
    )
    UserProfile.objects.create(
        user=staff,
        organization=org,
        role="STAFF"
    )

    instrument = Instrument.objects.create(
        organization=org,
        code="PHQ9",
        name="PHQ-9"
    )

    TestDefinition.objects.create(
        organization=org,
        instrument=instrument,
        code="PHQ9_STD",
        name="PHQ-9 Standard",
        language="en",
        json_schema={"type": "object"},
        scoring_spec={},
        is_active=True
    )

    panel = Panel.objects.create(
        organization=org,
        code="MENTAL_HEALTH_BASIC",
        name="Mental Health Basic Panel"
    )

    patient = Patient.objects.create(
        organization=org,
        name="Test Patient"
    )

    order = Order.objects.create(
        organization=org,
        patient=patient,
        panel=panel
    )

    session = Session.objects.create(
        organization=org,
        order=order,
        status="COMPLETED"
    )

    report = Report.objects.create(
        organization=org,
        session=session,
        status="READY",
        report_json={"result": "ok"}
    )

    release_url = f"/api/v1/reports/{report.id}/release/"

    # --------------------------------------------------
    # ❌ STAFF cannot release
    # --------------------------------------------------
    client.force_authenticate(user=staff)
    resp = client.post(release_url)
    assert resp.status_code == 403

    # --------------------------------------------------
    # ❌ CLINICIAN without signature → FAIL
    # --------------------------------------------------
    client.force_authenticate(user=clinician)
    resp = client.post(release_url)
    assert resp.status_code == 400
    assert "Signature required" in str(resp.data)

    # --------------------------------------------------
    # ✅ Add signature
    # --------------------------------------------------
    ReportSignature.objects.create(
        organization=org,
        report=report,
        signer_name="Dr. Test Clinician",
        signer_reg_no="CLN-12345",
        signer_role="CLINICIAN",
    )

    # --------------------------------------------------
    # ✅ CLINICIAN with signature → PASS
    # --------------------------------------------------
    resp = client.post(release_url)
    assert resp.status_code == 200
    assert resp.data["status"] == "released"

    # --------------------------------------------------
    # 🔒 Report remains immutable
    # --------------------------------------------------
    report.refresh_from_db()
    assert report.status == "READY"
