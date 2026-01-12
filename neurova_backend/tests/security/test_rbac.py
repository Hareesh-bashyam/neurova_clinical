import pytest
from rest_framework.test import APIClient

from django.contrib.auth.models import User

from core.models import Organization, UserProfile
from catalog.models import Instrument, TestDefinition, Panel
from patients.models import Patient
from orders.models import Order
from sessions.models import Session
from reports.models import Report, ReportSignature


@pytest.mark.django_db
def test_staff_cannot_release_report():
    """
    STAFF must NOT be allowed to release reports.
    Must return 403.
    """
    client = APIClient()

    org = Organization.objects.create(
        name="Org",
        code="ORG1",
        signature_required=True
    )

    staff = User.objects.create_user("staff@test.com", "pass")
    UserProfile.objects.create(
        user=staff,
        organization=org,
        role="STAFF"
    )

    clinician = User.objects.create_user("clin@test.com", "pass")
    UserProfile.objects.create(
        user=clinician,
        organization=org,
        role="CLINICIAN"
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
        report_json={"ok": True}
    )

    # even with signature, STAFF cannot release
    ReportSignature.objects.create(
        organization=org,
        report=report,
        signer_name="Dr Clinician",
        signer_reg_no="CLN-001",
        signer_role="CLINICIAN"
    )

    client.force_authenticate(user=staff)
    resp = client.post(f"/api/v1/reports/{report.id}/release/")

    assert resp.status_code == 403


@pytest.mark.django_db
def test_clinician_can_release_report():
    """
    CLINICIAN can release report when signature exists.
    Immutable semantics must be preserved.
    """
    client = APIClient()

    org = Organization.objects.create(
        name="Org",
        code="ORG2",
        signature_required=True
    )

    clinician = User.objects.create_user("clin@test.com", "pass")
    UserProfile.objects.create(
        user=clinician,
        organization=org,
        role="CLINICIAN"
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
        report_json={"ok": True}
    )

    # required signature
    ReportSignature.objects.create(
        organization=org,
        report=report,
        signer_name="Dr Clinician",
        signer_reg_no="CLN-001",
        signer_role="CLINICIAN"
    )

    client.force_authenticate(user=clinician)
    resp = client.post(f"/api/v1/reports/{report.id}/release/")

    assert resp.status_code == 200

    # Immutable record remains unchanged
    report.refresh_from_db()
    assert report.status == "READY"
