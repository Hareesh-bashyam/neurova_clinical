import pytest
from rest_framework.test import APIClient
from django.contrib.auth.models import User

from core.models import Organization, UserProfile
from catalog.models import Instrument, TestDefinition, Panel
from patients.models import Patient
from orders.models import Order
from sessions.models import Session
from reports.models import Report, ReportSignature
from auditlogs.models import AuditLog


@pytest.mark.django_db
def test_audit_log_coverage():
    """
    C4 — AUDIT LOG COVERAGE

    Phase-C guarantee:
    - ORDER_CREATED is audited
    - REPORT_RELEASED is audited

    Other lifecycle events are NOT required
    until explicit hooks exist.
    """

    client = APIClient()

    # --------------------------------------------------
    # Org + Clinician
    # --------------------------------------------------
    org = Organization.objects.create(
        name="Audit Org",
        code="AUDIT_ORG"
    )

    clinician = User.objects.create_user("clin@test.com", "pass")
    UserProfile.objects.create(
        user=clinician,
        organization=org,
        role="CLINICIAN"
    )

    client.force_authenticate(user=clinician)

    # --------------------------------------------------
    # Catalog setup
    # --------------------------------------------------
    instrument = Instrument.objects.create(
        organization=org,
        code="PHQ9",
        name="PHQ-9"
    )

    TestDefinition.objects.create(
        organization=org,
        instrument=instrument,
        code="PHQ9_STD",
        name="PHQ-9",
        language="en",
        json_schema={"type": "object"},
        scoring_spec={},
        is_active=True
    )

    panel = Panel.objects.create(
        organization=org,
        code="PANEL1",
        name="Panel"
    )

    patient = Patient.objects.create(
        organization=org,
        name="Patient"
    )

    # --------------------------------------------------
    # ORDER_CREATED (API)
    # --------------------------------------------------
    resp = client.post(
        "/api/v1/orders/",
        {
            "patient_id": patient.id,
            "panel_code": panel.code
        },
        format="json"
    )
    assert resp.status_code in (200, 201)

    order = Order.objects.get(patient=patient)

    # --------------------------------------------------
    # Minimal flow to reach report release
    # --------------------------------------------------
    session = Session.objects.create(
        organization=org,
        order=order,
        status="COMPLETED"
    )

    report = Report.objects.create(
        organization=org,
        session=session,
        status="READY",
        report_json={"ok": True}
    )

    ReportSignature.objects.create(
        organization=org,
        report=report,
        signer_name="Dr Clinician",
        signer_reg_no="CLN-001",
        signer_role="CLINICIAN"
    )

    resp = client.post(f"/api/v1/reports/{report.id}/release/")
    assert resp.status_code == 200

    # --------------------------------------------------
    # ASSERT AUDIT EVENTS (PHASE-C SCOPE)
    # --------------------------------------------------
    expected_actions = {
        "ORDER_CREATED",
        "REPORT_RELEASED",
    }

    logged_actions = set(
        AuditLog.objects.filter(organization=org)
        .values_list("action", flat=True)
    )

    missing = expected_actions - logged_actions
    assert not missing, f"Missing audit events: {missing}"
