
import sys
import types
from unittest.mock import MagicMock

def verify_logic():
    print("Starting standalone mock verification...")
    
    # 1. READ FILE CONTENT
    report_context_path = "apps/clinical_ops/services/report_context.py"
    try:
        with open(report_context_path, "r", encoding="utf-8") as f:
            report_context_code = f.read()
    except FileNotFoundError:
        print(f"Could not find {report_context_path}. Running from wrong directory?")
        return

    # 2. MOCK DEPENDENCIES
    # We need to mock the imports inside report_context.py
    
    # Create a dummy module for apps.clinical_ops.models
    mock_models = types.ModuleType("apps.clinical_ops.models")
    mock_models.AssessmentOrder = MagicMock()
    sys.modules["apps.clinical_ops.models"] = mock_models
    
    mock_assess = types.ModuleType("apps.clinical_ops.models_assessment")
    mock_assess.AssessmentResult = MagicMock()
    sys.modules["apps.clinical_ops.models_assessment"] = mock_assess
    
    mock_report = types.ModuleType("apps.clinical_ops.models_report")
    mock_report.AssessmentReport = MagicMock()
    sys.modules["apps.clinical_ops.models_report"] = mock_report
    
    mock_django_utils = types.ModuleType("django.utils.timezone")
    mock_django_utils.localtime = lambda x: x # Mock localtime
    sys.modules["django.utils.timezone"] = mock_django_utils
    
    # exec the code to get the function
    context_scope = {}
    try:
        exec(report_context_code, context_scope)
    except Exception as e:
        print(f"Error executing report_context code: {e}")
        return

    build_report_context = context_scope.get("build_report_context")
    if not build_report_context:
        print("Could not find build_report_context function")
        return

    # 3. VERIFY REPORT CONTEXT LOGIC
    print("Verifying build_report_context logic...")
    
    # Setup mocks for the function call
    mock_order = MagicMock()
    mock_order.patient_acceptance_remark = "TEST_REMARK_CONTENT"
    mock_order.status = "COMPLETED"
    
    # Mock AssessmentResult.objects.get(order=order)
    mock_result_obj = MagicMock()
    mock_result_obj.result_json = {"summary": {"primary_severity": "Low"}}
    
    # We need to ensure when AssessmentResult.objects.get is called, it returns our mock
    # The code uses: AssessmentResult.objects.get(order=order)
    # logic inside report_context.py imports AssessmentResult from apps.clinical_ops.models_assessment
    # We mocked that module.
    
    context_scope["AssessmentResult"].objects.get.return_value = mock_result_obj
    
    # Mock AssessmentReport.DoesNotExist
    context_scope["AssessmentReport"].DoesNotExist = Exception
    context_scope["AssessmentReport"].objects.get.side_effect = Exception("No Report")

    # CALL FUNCTION
    try:
        ctx = build_report_context(mock_order)
        print(f"Context keys: {list(ctx.keys())}")
        remarks = ctx.get("remarks")
        print(f"Remarks: {remarks}")
        
        if remarks == "TEST_REMARK_CONTENT":
            print("SUCCESS: Remarks correctly extracted into context.")
        else:
            print("FAILED: Remarks mismatch.")
            
    except Exception as e:
        print(f"Error calling build_report_context: {e}")
        import traceback
        traceback.print_exc()

    
    # 4. VERIFY PDF GENERATION LOGIC
    # Similar approach for pdf_report_v2.py
    pdf_path = "apps/clinical_ops/services/pdf_report_v2.py"
    with open(pdf_path, "r", encoding="utf-8") as f:
        pdf_code = f.read()
        
    # Mocks for PDF
    mock_rl = MagicMock()
    sys.modules["reportlab"] = mock_rl
    sys.modules["reportlab.lib.pagesizes"] = MagicMock()
    sys.modules["reportlab.lib.units"] = MagicMock()
    sys.modules["reportlab.lib.colors"] = MagicMock()
    sys.modules["reportlab.lib.styles"] = MagicMock()
    sys.modules["reportlab.platypus"] = MagicMock()
    sys.modules["reportlab.lib.enums"] = MagicMock()
    
    pdf_scope = {}
    
    # We need to mock reportlab flowables to capture if remarks are added
    # The code does: elements.append(Paragraph(...))
    
    # Let's inspect the code for the presence of the remarks section logic
    if 'remarks = report_context.get("remarks")' in pdf_code and 'Paragraph("Remarks", H2)' in pdf_code:
         print("SUCCESS: PDF code contains remarks handling logic (Static check).")
    else:
         print("FAILED: PDF code missing remarks handling logic.")

if __name__ == "__main__":
    verify_logic()
