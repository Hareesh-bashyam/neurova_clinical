from django.core.management.base import BaseCommand
from django.test import RequestFactory
from apps.clinical_ops.models import AssessmentOrder, Patient, Organization, PublicAccessToken
from apps.clinical_ops.services.public_token_validator import validate_and_rotate_url_token
from django.utils import timezone
import secrets

class Command(BaseCommand):
    help = 'Reproduce token rotation issue'

    def handle(self, *args, **options):
        # Setup
        org, _ = Organization.objects.get_or_create(name="Test Rotation Org")
        patient = Patient.objects.create(org=org, full_name="Rotation Patient", age=30, sex="MALE")
        
        initial_token = secrets.token_urlsafe(32)
        order = AssessmentOrder.objects.create(
            org=org, 
            patient=patient, 
            battery_code="TEST",
            public_token=initial_token
        )
        
        # Create initial PublicAccessToken
        PublicAccessToken.objects.create(
            order=order,
            token_hash=PublicAccessToken.hash_token(initial_token),
            expires_at=timezone.now() + timezone.timedelta(hours=1)
        )
        
        print(f"Initial Token: {initial_token}")
        print(f"Order DB Token: {order.public_token}")
        
        # Simulate Request
        factory = RequestFactory()
        request = factory.get('/')
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        request.META['HTTP_USER_AGENT'] = 'TestAgent'
        
        # Rotate
        print("--- Rotating Token ---")
        try:
            _, new_token = validate_and_rotate_url_token(initial_token, request)
            order.refresh_from_db()
            
            print(f"New Token Returned: {new_token}")
            print(f"Order DB Token After Rotation: {order.public_token}")
            
            if order.public_token == new_token:
                print("SUCCESS: Order token updated.")
            else:
                print("FAILURE: Order token NOT updated.")
                
        except Exception as e:
            print(f"Error: {e}")
