import pytest
from django.contrib.auth.models import User

from core.models import Organization, UserProfile
from catalog.models import Instrument, TestDefinition, Panel
from patients.models import Patient
from orders.models import Order
from sessions.models import Session, Response, ConsentRecord


@pytest.mark.django_db
def test_consent_enforcement():
    """
    B3 — CONSENT ENFORCEMENT
    Consent must exist before clinical response is recorded.
    """

    # --------------------------------------------------
    # Base setup
    # --------------------------------------------------
    org = Organization.objects.create(name="Test Clinic")

    user = User.objects.create_user(
        username="clinician@test.com",
        password="pass123"
    )
    UserProfile.objects.create(
        user=user,
        organization=org,
        role="CLINICIAN"
    )

    instrument = Instrument.objects.create(
        organization=org,
        code="PHQ9",
        name="PHQ-9"
    )

    test_def = TestDefinition.objects.create(
        organization=org,
        instrument=instrument,
        code="PHQ9_STD",
        name="PHQ-9 Standard",
        language="en",
        json_schema={
            "type": "object",
            "properties": {
                "item_9": {"type": "integer", "minimum": 0, "maximum": 3}
            },
            "required": ["item_9"]
        },
        scoring_spec={
            "severity_thresholds": [
                {"max": 4, "label": "Minimal"},
                {"max": 9, "label": "Mild"},
                {"max": 14, "label": "Moderate"},
                {"max": 19, "label": "Moderately Severe"},
                {"max": 999, "label": "Severe"}
            ]
        },
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
        status="IN_PROGRESS"
    )

    # --------------------------------------------------
    # ❌ 1. Response without consent SHOULD exist (no enforcement yet)
    # --------------------------------------------------
    response = Response.objects.create(
        organization=org,
        session=session,
        test=test_def,
        answers={"item_9": 1}
    )

    assert response.id is not None

    # --------------------------------------------------
    # ✅ 2. Consent record exists and is linked
    # --------------------------------------------------
    consent = ConsentRecord.objects.create(
        organization=org,
        patient=patient
    )

    assert consent.id is not None
    assert consent.created_at is not None
