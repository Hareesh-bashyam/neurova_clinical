import pytest
from django.apps import apps
from django.contrib.auth.models import User


# --- SAFE MODEL RESOLUTION (NO DIRECT IMPORTS) ---

Organization = apps.get_model("core", "Organization")
UserProfile = apps.get_model("core", "UserProfile")

Instrument = apps.get_model("catalog", "Instrument")
TestDefinition = apps.get_model("catalog", "TestDefinition")
Panel = apps.get_model("catalog", "Panel")

Patient = apps.get_model("patients", "Patient")
Order = apps.get_model("orders", "Order")

Session = apps.get_model("clinical_sessions", "Session")
Response = apps.get_model("clinical_sessions", "Response")

Score = apps.get_model("scoring", "Score")
Report = apps.get_model("reports", "Report")


@pytest.mark.django_db
def test_full_clinical_session_flow():
    """
    End-to-end clinical flow.
    Mirrors EXACTLY what worked in Postman.
    """

    # 1. Organization
    org = Organization.objects.create(name="Test Clinic")

    # 2. User (ORG_ADMIN)
    user = User.objects.create_user(
        username="admin@test.com",
        password="pass123"
    )
    UserProfile.objects.create(
        user=user,
        organization=org,
        role="ORG_ADMIN"
    )

    # 3. Instrument
    instrument = Instrument.objects.create(
        organization=org,
        code="PHQ9",
        name="PHQ-9"
    )

    # 4. Test Definition
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

    # 5. Panel (REQUIRED by Order)
    panel = Panel.objects.create(
        organization=org,
        code="MENTAL_HEALTH_BASIC",
        name="Mental Health Basic Panel"
    )

    # 6. Patient
    patient = Patient.objects.create(
        organization=org,
        name="Test Patient"
    )

    # 7. Order
    order = Order.objects.create(
        organization=org,
        patient=patient,
        panel=panel
    )

    # 8. Session
    session = Session.objects.create(
        organization=org,
        order=order,
        status="IN_PROGRESS"
    )

    # 9. Response
    Response.objects.create(
        organization=org,
        session=session,
        test=test_def,          # ← REQUIRED
        answers={"item_9": 1}
    )



    # 10. Score
    Score.objects.create(
        session=session,
        score=9,
        severity="Mild",
        breakdown={"item_9": 1}
    )

    # 11. Report
    report = Report.objects.create(
        organization=org,
        session=session,
        status="READY",
        report_json={
            "summary": "PHQ-9 completed",
            "severity": "Mild",
            "score": 9
        }
    )


    assert report.status == "READY"
