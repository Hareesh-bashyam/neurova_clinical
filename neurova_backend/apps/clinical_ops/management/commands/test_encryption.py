from django.core.management.base import BaseCommand
from rest_framework.test import APIRequestFactory, force_authenticate
from apps.clinical_ops.api.v1.inbox_views import ClinicalInboxView
from apps.clinical_ops.models import AssessmentOrder, Patient, Organization, AssessmentResult
from django.contrib.auth.models import User
from apps.clinical_ops.models import Org  # Adjust if Org model is different
from core.models import UserProfile # Adjust based on actual UserProfile model location
from django.utils import timezone
import json

class Command(BaseCommand):
    help = 'Reproduce encryption issue in ClinicalInboxView'

    def handle(self, *args, **options):
        # 1. Setup Data
        org, _ = Organization.objects.get_or_create(name="Encryption Test Org")
        
        # Create User
        username = "enc_test_user"
        email = "enc_test@example.com"
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User.objects.create_user(username=username, email=email, password="password123")
            # Create Profile if needed (based on views.py: request.user.profile.organization)
            # Assuming UserProfile exists and has organization field
            try:
                profile, _ = UserProfile.objects.get_or_create(user=user, organization=org)
            except Exception as e:
                print(f"Profile creation error (might be auto-created): {e}")

        # Create Patient & Order
        patient = Patient.objects.create(org=org, full_name="Enc Patient", age=40, sex="FEMALE")
        order = AssessmentOrder.objects.create(
            org=org,
            patient=patient,
            status=AssessmentOrder.STATUS_COMPLETED,
            battery_code="TEST_BATTERY",
            created_at=timezone.now()
        )
        # Mock result
        AssessmentResult.objects.create(order=order, primary_severity="MODERATE", has_red_flags=True)

        # 2. Simulate Request
        factory = APIRequestFactory()
        request = factory.get('/api/v1/staff/inbox')
        force_authenticate(request, user=user)
        
        view = ClinicalInboxView.as_view()
        response = view(request)
        
        print(f"Status Code: {response.status_code}")
        if hasattr(response, 'data'):
            print("Response Data Keys:", response.data.keys())
            if 'encrypted_data' in response.data:
                print("SUCCESS: Response is encrypted.")
                print(f"Encrypted Data Snippet: {str(response.data['encrypted_data'])[:50]}...")
            elif 'data' in response.data:
                print("FAILURE: Response is RAW (Unencrypted).")
                print(f"Raw Data: {response.data['data']}")
            else:
                print("Unexpected response structure.")
        else:
            print("Response has no data attribute.")
