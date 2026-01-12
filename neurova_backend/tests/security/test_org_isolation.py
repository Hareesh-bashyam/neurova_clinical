import pytest
from rest_framework.test import APIClient
from django.contrib.auth.models import User

from core.models import Organization, UserProfile
from patients.models import Patient


@pytest.mark.django_db
def test_org_isolation():
    client = APIClient()

    # -------------------------
    # Org A
    # -------------------------
    org_a = Organization.objects.create(
        name="Org A",
        code="ORG_A"
    )

    user_a = User.objects.create_user("a@test.com", "pass")
    UserProfile.objects.create(
        user=user_a,
        organization=org_a,
        role="CLINICIAN"
    )

    patient_a = Patient.objects.create(
        organization=org_a,
        name="Patient A"
    )

    # -------------------------
    # Org B
    # -------------------------
    org_b = Organization.objects.create(
        name="Org B",
        code="ORG_B"
    )

    user_b = User.objects.create_user("b@test.com", "pass")
    UserProfile.objects.create(
        user=user_b,
        organization=org_b,
        role="CLINICIAN"
    )

    client.force_authenticate(user=user_b)

    # ❌ Org B GET patient of Org A → 404
    resp = client.get(f"/api/v1/patients/{patient_a.id}/")
    assert resp.status_code == 404

    # ❌ Org B list sessions → endpoint not exposed → 404 (SECURE)
    resp = client.get("/api/v1/sessions/")
    assert resp.status_code == 404
