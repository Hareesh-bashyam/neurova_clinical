import uuid
import pytest
from django.test import Client
from backend.clinical.org.models import Organization

@pytest.mark.django_db
def test_org_isolation_blocks_cross_org_access():
    c = Client()

    org_a = Organization.objects.create(id=uuid.uuid4(), name="OrgA", address="A")
    org_b = Organization.objects.create(id=uuid.uuid4(), name="OrgB", address="B")

    # create order in OrgA
    resp = c.post("/api/v1/clinical/orders/",
                  data={
                      "organization_id": str(org_a.id),
                      "patient_name": "P",
                      "patient_age": 30,
                      "patient_gender": "Male",
                      "encounter_type": "OPD",
                      "administration_mode": "IN_CLINIC",
                      "battery_code": "ANX_SCREEN_V1"
                  },
                  content_type="application/json",
                  **{"HTTP_X_ORG_ID": str(org_a.id)}
                  )
    assert resp.status_code in (200,201)
    order_id = resp.json()["data"]["order_id"]

    # try fetch pdf with OrgB header (must 404/403)
    resp2 = c.get(f"/api/v1/clinical/orders/{order_id}/pdf/", **{"HTTP_X_ORG_ID": str(org_b.id)})
    assert resp2.status_code in (403,404)
