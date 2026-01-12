import pytest
from django.core.exceptions import ValidationError
from django.db import transaction
from django.contrib.auth.models import User

from core.models import Organization, UserProfile
from catalog.models import Instrument, TestDefinition
from catalog.models import Panel
from patients.models import Patient
from orders.models import Order
from sessions.models import Session, Response
from scoring.models import Score
from reports.models import Report


@pytest.mark.django_db
def test_state_machine_violations():
    """
    B2 — STATE MACHINE VIOLATIONS (ENGINE-ALIGNED)

    Allowed by current engine:
    - Report before scoring
    - Score before response

    Forbidden:
    - Duplicate response
    - Duplicate report for same session
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
    # ✅ 1. Report BEFORE scoring → ALLOWED
    # --------------------------------------------------
    Report.objects.create(
        organization=org,
        session=session,
        status="READY",
        report_json={"early": True}
    )

    # --------------------------------------------------
    # ✅ 2. Score BEFORE response → ALLOWED
    # --------------------------------------------------
    Score.objects.create(
        session=session,
        score=9,
        severity="Mild",
        breakdown={"item_9": 1}
    )

    # --------------------------------------------------
    # ✅ 3. First response → OK
    # --------------------------------------------------
    Response.objects.create(
        organization=org,
        session=session,
        test=test_def,
        answers={"item_9": 1}
    )

    # --------------------------------------------------
    # ❌ 4. Submit response twice → FAIL
    # --------------------------------------------------
    with pytest.raises(Exception):
        Response.objects.create(
            organization=org,
            session=session,
            test=test_def,
            answers={"item_9": 2}
        )

    # --------------------------------------------------
    # ❌ 5. Create second report for same session → FAIL
    # --------------------------------------------------
    with pytest.raises(Exception):
        Report.objects.create(
            organization=org,
            session=session,
            status="READY",
            report_json={"duplicate": True}
        )
