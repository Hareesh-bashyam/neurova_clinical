from django.test import TestCase
from apps.clinical_ops.models import Org, Patient, AssessmentOrder
import secrets
from django.utils import timezone

class ClinicalOpsTests(TestCase):
    def test_create_order_and_queue(self):
        org = Org.objects.create(name="Org1")
        patient = Patient.objects.create(org=org, full_name="A", age=30, sex="Male")
        order = AssessmentOrder.objects.create(
            org=org, patient=patient,
            battery_code="MENTAL_HEALTH_CORE_V1",
            battery_version="1.0",
            public_token=secrets.token_urlsafe(16),
            public_link_expires_at=timezone.now() + timezone.timedelta(days=2),
        )
        self.assertEqual(order.status, AssessmentOrder.STATUS_CREATED)
