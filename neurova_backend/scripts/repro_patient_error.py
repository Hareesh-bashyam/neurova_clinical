
import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "neurova_backend.settings")
django.setup()

from patients.serializers import PatientSerializer
from core.models import Organization
from django.contrib.auth.models import User
from core.models import UserProfile

class MockRequest:
    def __init__(self, user):
        self.user = user
        self.META = {"REMOTE_ADDR": "127.0.0.1", "HTTP_USER_AGENT": "Script"}

from auditlogs.utils import log_event

def repro():
    print("Starting reproduction...")
    try:
        user = User.objects.get(username="admin")
    except User.DoesNotExist:
        print("Admin user not found. Run setup_admin.py first.")
        return

    req = MockRequest(user)
    org = user.profile.organization
    print(f"Using org: {org}")

    data = {
        "name": "Repro Patient",
        "dob": "1990-01-01",
        "sex": "MALE",
        "email": "repro@test.com"
    }
    
    serializer = PatientSerializer(data=data)
    if serializer.is_valid():
        print("Serializer is valid.")
        try:
            print("Attempting to save with organization injection...")
            serializer.save(organization=org)
            patient = serializer.instance
            print("✅ Patient created successfully!")
            
            print("Attempting to log event...")
            log_event(
                request=req,
                org=patient.organization,
                action="PATIENT_CREATED",
                entity_type="Patient",
                entity_id=patient.id,
            )
            print("✅ Audit log created successfully!")
            
        except Exception as e:
            print("\n❌ CAUGHT EXCEPTION during save/log:")
            print(e)
            import traceback
            traceback.print_exc()
    else:
        print("Serializer invalid:", serializer.errors)

if __name__ == "__main__":
    repro()
