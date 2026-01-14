import uuid
import pytest
from backend.clinical.org.models import Organization
from backend.clinical.models import ClinicalOrder, BatterySession, TestRun
from backend.clinical.reporting.report_builder_v1 import generate_report_for_order_v1
from django.utils import timezone

@pytest.mark.django_db
def test_report_is_immutable_after_generation():
    org = Organization.objects.create(id=uuid.uuid4(), name="Org", address="Addr")

    order = ClinicalOrder.objects.create(
        organization_id=org.id,
        patient_name="P",
        patient_age=30,
        patient_gender="Male",
        encounter_type="OPD",
        administration_mode="IN_CLINIC",
        battery_code="ANX_SCREEN_V1",
        battery_version="1.0",
        status="COMPLETED"
    )
    sess = BatterySession.objects.create(organization_id=org.id, order=order, status="COMPLETED", current_test_index=0, started_at=timezone.now(), completed_at=timezone.now())
    tr = TestRun.objects.create(organization_id=org.id, session=sess, test_code="GAD7", test_order_index=0, raw_responses=[0,0,0,0,0,0,0], time_submitted=timezone.now())

    r1 = generate_report_for_order_v1(order)
    rid1 = r1.report_json["report_id"]

    r2 = generate_report_for_order_v1(order)
    rid2 = r2.report_json["report_id"]

    assert rid1 == rid2
