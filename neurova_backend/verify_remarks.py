
import os
import sys
import django
from django.conf import settings
from django.utils import timezone
from unittest.mock import MagicMock

# Setup Django if not already (though running via shell handles this)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "neurova_backend.settings")
django.setup()

from apps.clinical_ops.services.report_context import build_report_context
from apps.clinical_ops.services.pdf_report_v2 import generate_report_pdf_bytes_v2
from apps.clinical_ops.models import AssessmentOrder, Patient
from apps.clinical_ops.models_assessment import AssessmentResult
from apps.clinical_ops.models_report import AssessmentReport
from core.models import Organization

def verify_remarks_in_report():
    print("Starting verification of remarks in report...")

    # Mock objects to avoid DB dependency for this test if possible, 
    # but `build_report_context` queries DB (AssessmentResult.objects.get(order=order))
    # so we might need real objects or extensive mocking.
    # Let's try to mock the DB calls if possible, or just create dummy data if DB is accessible.
    
    # Assuming we are in a dev environment with DB access.
    # Let's try to create a dummy order.
    
    try:
        # 1. Create Data
        org, _ = Organization.objects.get_or_create(name="Test Org", defaults={"is_active": True})
        patient = Patient.objects.create(
            org=org, full_name="Test Patient", age=30, sex="Male", mrn="TEST-MRN"
        )
        order = AssessmentOrder.objects.create(
            org=org, patient=patient, battery_code="TEST_BATTERY", 
            status="COMPLETED", patient_acceptance_remark="Patient says they are fine."
        )
        
        # Create Result
        result_json = {
            "summary": {"primary_severity": "Mild", "has_red_flags": False},
            "per_test": {"TEST1": {"score": 10, "severity": "Normal"}}
        }
        AssessmentResult.objects.create(org=org, order=order, result_json=result_json)
        
        # Create Report (optional but context uses it)
        AssessmentReport.objects.create(org=org, order=order)

        # 2. Test Context
        print("Testing build_report_context...")
        ctx = build_report_context(order)
        
        if "remarks" not in ctx:
            print("FAILED: 'remarks' key missing in context")
            return
        
        if ctx["remarks"] != "Patient says they are fine.":
            print(f"FAILED: 'remarks' value mismatch. Got: {ctx['remarks']}")
            return
            
        print("SUCCESS: Context contains correct remarks.")

        # 3. Test PDF Generation
        print("Testing generate_report_pdf_bytes_v2...")
        pdf_bytes = generate_report_pdf_bytes_v2(ctx)
        
        if not pdf_bytes or len(pdf_bytes) == 0:
            print("FAILED: PDF bytes empty")
            return
            
        print(f"SUCCESS: PDF generated successfully ({len(pdf_bytes)} bytes).")
        
        # Cleanup
        order.delete()
        patient.delete()
        # Org might be shared, keeping it.

    except Exception as e:
        print(f"ERROR during verification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_remarks_in_report()
