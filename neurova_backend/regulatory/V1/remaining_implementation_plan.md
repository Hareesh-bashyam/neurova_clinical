# Remaining Implementation Plan - High Priority Tasks

**Document Version:** 1.0  
**Date:** 2026-02-14  
**Estimated Total Time:** 3.5 hours  
**Status:** Ready for implementation

---

## Task 1: PDF Watermarking (2 hours)

### Objective
Add "PROVISIONAL – NOT CLINICALLY REVIEWED" watermark to PDF reports that have critical flags or are awaiting review.

### Files to Modify
1. `apps/clinical_ops/services/pdf_report_v2.py`

### Implementation Steps

#### Step 1.1: Create Watermark Function (30 min)
```python
from reportlab.lib.colors import Color

def add_watermark_to_canvas(canvas, doc, report_status):
    """
    Add watermark to PDF pages if report is PROVISIONAL.
    
    Args:
        canvas: ReportLab canvas object
        doc: Document object
        report_status: Status of the report (DRAFT/PROVISIONAL/REVIEWED)
    """
    if report_status == 'PROVISIONAL':
        canvas.saveState()
        
        # Set watermark properties
        canvas.setFont("Helvetica-Bold", 60)
        canvas.setFillColor(Color(1, 0, 0, alpha=0.2))  # Red, 20% opacity
        
        # Calculate center position
        page_width = doc.pagesize[0]
        page_height = doc.pagesize[1]
        
        # Rotate and draw watermark diagonally
        canvas.translate(page_width / 2, page_height / 2)
        canvas.rotate(45)
        
        # Draw watermark text
        watermark_text = "PROVISIONAL – NOT CLINICALLY REVIEWED"
        canvas.drawCentredString(0, 0, watermark_text)
        
        canvas.restoreState()
```

#### Step 1.2: Determine Report Status (15 min)
```python
def determine_report_status(report_context: dict) -> str:
    """
    Determine report status based on flags and review state.
    
    Returns:
        'DRAFT' - Screening in progress
        'PROVISIONAL' - Completed but has critical flags OR awaiting review
        'REVIEWED' - Clinician has reviewed and signed off
    """
    # Check if reviewed
    if report_context.get('reviewed_at'):
        return 'REVIEWED'
    
    # Check for critical flags
    has_critical_flags = report_context.get('has_critical_flags', False)
    
    # Check if completed
    is_completed = report_context.get('status') == 'COMPLETED'
    
    if is_completed and (has_critical_flags or not report_context.get('reviewed_at')):
        return 'PROVISIONAL'
    
    return 'DRAFT'
```

#### Step 1.3: Integrate Watermark into PDF Generation (45 min)
```python
def generate_report_pdf_bytes_v2(report_context: dict) -> tuple[bytes, str]:
    """
    Generate PDF report with watermark if PROVISIONAL.
    
    Returns:
        tuple: (pdf_bytes, sha256_hash)
    """
    buf = io.BytesIO()
    
    # Determine report status
    report_status = determine_report_status(report_context)
    
    # Create document with watermark callback
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Build elements (existing code)
    elements = []
    # ... existing PDF building code ...
    
    # Build PDF with watermark
    doc.build(
        elements,
        onFirstPage=lambda c, d: add_watermark_to_canvas(c, d, report_status),
        onLaterPages=lambda c, d: add_watermark_to_canvas(c, d, report_status)
    )
    
    # Get PDF bytes
    buf.seek(0)
    pdf_bytes = buf.read()
    
    # Calculate SHA-256 hash (see Task 2)
    sha256_hash = hashlib.sha256(pdf_bytes).hexdigest()
    
    return pdf_bytes, sha256_hash
```

#### Step 1.4: Update Report Generation View (30 min)
```python
# In apps/clinical_ops/api/v1/report_views.py

def generate_report(request, order_id):
    # ... existing code to get order and context ...
    
    # Add critical flags to context
    report_context['has_critical_flags'] = order.result.has_red_flags if hasattr(order, 'result') else False
    report_context['reviewed_at'] = order.reviewed_at if hasattr(order, 'reviewed_at') else None
    report_context['status'] = order.status
    
    # Generate PDF with watermark
    pdf_bytes, sha256_hash = generate_report_pdf_bytes_v2(report_context)
    
    # Save to AssessmentReport
    report = AssessmentReport.objects.create(
        org=order.org,
        order=order,
        sha256_hash=sha256_hash,  # Store hash
        # ... other fields ...
    )
    
    # Save PDF file
    report.pdf_file.save(f"report_{order.id}.pdf", ContentFile(pdf_bytes))
    
    # Log event
    log_event(
        org=order.org,
        event_type="REPORT_GENERATED",
        entity_type="AssessmentReport",
        entity_id=report.id,
        details={
            'order_id': order.id,
            'sha256_hash': sha256_hash,
            'has_watermark': report_context.get('has_critical_flags', False)
        },
        request=request
    )
```

### Testing Checklist
- [ ] Generate report with critical flags → Should have watermark
- [ ] Generate report without critical flags, not reviewed → Should have watermark
- [ ] Generate reviewed report → Should NOT have watermark
- [ ] Verify watermark is visible but doesn't obscure content
- [ ] Check watermark appears on all pages

---

## Task 2: SHA-256 Hash Fix (30 min)

### Objective
Fix SHA-256 hash to be full 64 characters and hash the final PDF bytes instead of payload JSON.

### Files to Modify
1. `apps/clinical_ops/services/pdf_report_v2.py`
2. `apps/clinical_ops/models_report.py` (verify field exists)

### Implementation Steps

#### Step 2.1: Remove Truncated Hash Function (5 min)
```python
# DELETE THIS FUNCTION
def _hash_payload(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]  # ❌ REMOVE
```

#### Step 2.2: Update generate_report_pdf_bytes_v2 (15 min)
```python
import hashlib

def generate_report_pdf_bytes_v2(report_context: dict) -> tuple[bytes, str]:
    """
    Generate PDF report and return bytes with SHA-256 hash.
    
    Returns:
        tuple: (pdf_bytes, sha256_hash)
    """
    buf = io.BytesIO()
    
    # ... existing PDF generation code ...
    doc.build(elements, onFirstPage=..., onLaterPages=...)
    
    # Get PDF bytes
    buf.seek(0)
    pdf_bytes = buf.read()
    
    # Calculate full SHA-256 hash of PDF bytes (not payload!)
    sha256_hash = hashlib.sha256(pdf_bytes).hexdigest()  # Full 64 chars
    
    return pdf_bytes, sha256_hash
```

#### Step 2.3: Update All Callers (10 min)
```python
# Find all places that call generate_report_pdf_bytes_v2
# Update to handle tuple return value

# Example in report generation view:
pdf_bytes, sha256_hash = generate_report_pdf_bytes_v2(report_context)

# Store hash in database
report.sha256_hash = sha256_hash
report.save()
```

### Verification Steps
- [ ] Hash is exactly 64 characters long
- [ ] Hash is stored in `AssessmentReport.sha256_hash` field
- [ ] Hash changes if PDF content changes
- [ ] Hash is same for identical PDF content
- [ ] Remove any references to `_hash_payload()` function

---

## Task 3: Verify log_event() Usage (1 hour)

### Objective
Ensure all API endpoints call `log_event()` with correct event types and include `app_version`.

### Files to Check
1. `apps/clinical_ops/api/v1/urls.py` - Get list of all endpoints
2. All view files in `apps/clinical_ops/api/v1/`

### API Endpoints to Verify (14 total)

#### Step 3.1: Create Verification Checklist (10 min)

| Endpoint | View | Event Type | Status |
|----------|------|------------|--------|
| `staff/patients/create` | CreatePatient | PATIENT_CREATED | ⬜ |
| `staff/orders/create` | CreateOrder | ORDER_CREATED | ⬜ |
| `staff/orders/<id>/start` | StartOrder | ORDER_STARTED | ⬜ |
| `public/order/<token>/consent` | PublicSubmitConsent | CONSENT_SUBMITTED | ⬜ |
| `public/order/<token>/submit` | PublicSubmitAssessment | ASSESSMENT_SUBMITTED | ⬜ |
| `staff/orders/<id>/report/generate` | GenerateReport | REPORT_GENERATED | ⬜ |
| `staff/orders/<id>/report/pdf` | DownloadReport | PDF_DOWNLOADED | ⬜ |
| `public/order/<token>/report.pdf` | PublicDownloadReport | PDF_EXPORTED | ⬜ |
| `staff/reports/signoff/override` | OverrideReportSignoff | REPORT_SIGNOFF_OVERRIDE | ⬜ |
| `public/order/<token>/report/access-code` | PublicRequestReportCode | REPORT_ACCESS_REQUESTED | ⬜ |
| `admin/data-deletion/approve` | AdminApproveDeletion | DATA_DELETION_APPROVED | ⬜ |
| `staff/orders/<id>/cancel` | CancelOrder | ORDER_CANCELLED | ⬜ |
| `staff/orders/<id>/deliver` | DeliverReport | REPORT_DELIVERED | ⬜ |
| `public/order/<token>/validate` | ValidateToken | TOKEN_VALIDATED | ⬜ |

#### Step 3.2: Verify Each Endpoint (40 min)

For each endpoint, check:

```python
# ✅ GOOD EXAMPLE
def create_patient(request):
    # ... business logic ...
    
    log_event(
        org=org,
        event_type="PATIENT_CREATED",
        entity_type="Patient",
        entity_id=patient.id,
        actor_user_id=request.user.id,
        actor_name=request.user.get_full_name(),
        actor_role=request.user.role,
        details={'patient_mrn': patient.mrn},
        request=request,
        severity="INFO"
        # app_version is automatically captured from settings
    )
    
    return Response(...)

# ❌ BAD EXAMPLE - Missing log_event
def some_endpoint(request):
    # ... business logic ...
    return Response(...)  # No audit event!
```

#### Step 3.3: Create Audit Event Summary (10 min)

Create a file documenting all audit events:

```markdown
# Audit Events Summary

## Event Types Used

1. **PATIENT_CREATED** - Patient record created by staff
2. **ORDER_CREATED** - Assessment order created
3. **CONSENT_SUBMITTED** - Patient submitted consent
4. **ASSESSMENT_SUBMITTED** - Patient completed assessment
5. **REPORT_GENERATED** - PDF report generated
6. **PDF_DOWNLOADED** - Staff downloaded PDF
7. **PDF_EXPORTED** - Public user accessed PDF
8. **REPORT_SIGNOFF_OVERRIDE** - Manual signoff override
9. **DATA_DELETION_APPROVED** - Admin approved data deletion
10. **ORDER_CANCELLED** - Order cancelled
11. **REPORT_DELIVERED** - Report delivered to patient

## Severity Levels
- INFO: Normal operations
- WARNING: Unusual but not critical
- ERROR: Failed operations
- SECURITY: Security-related events (access denials, suspicious activity)
```

### Testing Checklist
- [ ] All 14 endpoints have `log_event()` calls
- [ ] Event types are descriptive and consistent
- [ ] `app_version` is automatically captured
- [ ] Sensitive data is NOT logged in details
- [ ] Failed operations log with severity="ERROR"
- [ ] Security events log with severity="SECURITY"

---

## Task 4: Integration Testing (Bonus - 30 min)

### Test Scenarios

#### Scenario 1: PROVISIONAL Report with Watermark
```python
# Test case
1. Create order with critical flags
2. Generate report
3. Verify:
   - PDF has watermark
   - SHA-256 hash is 64 chars
   - Hash stored in database
   - Audit event logged with app_version
```

#### Scenario 2: REVIEWED Report without Watermark
```python
# Test case
1. Create order
2. Generate report
3. Mark as reviewed
4. Regenerate report
5. Verify:
   - PDF has NO watermark
   - New SHA-256 hash
   - Audit events logged
```

#### Scenario 3: Audit Trail Completeness
```python
# Test case
1. Perform full workflow (create → consent → submit → generate → download)
2. Query audit events
3. Verify:
   - All events logged
   - app_version present in all events
   - Timestamps correct
   - No missing events
```

---

## Rollout Plan

### Phase 1: Development (3.5 hours)
1. ✅ Implement PDF watermarking (2 hours)
2. ✅ Fix SHA-256 hash (30 min)
3. ✅ Verify log_event() usage (1 hour)

### Phase 2: Testing (1 hour)
1. Manual testing of watermark scenarios
2. Verify hash storage
3. Check audit logs

### Phase 3: Code Review (30 min)
1. Review changes with team
2. Verify regulatory compliance
3. Update documentation

### Phase 4: Deployment (30 min)
1. Run migration (if needed)
2. Deploy to staging
3. Smoke test
4. Deploy to production

---

## Success Criteria

### PDF Watermarking ✅
- [ ] Watermark appears on PROVISIONAL reports
- [ ] Watermark does NOT appear on REVIEWED reports
- [ ] Watermark is visible but doesn't obscure content
- [ ] Watermark appears on all pages

### SHA-256 Hash ✅
- [ ] Hash is exactly 64 characters
- [ ] Hash is calculated from PDF bytes (not JSON)
- [ ] Hash is stored in database
- [ ] Hash is unique for different PDFs

### Audit Logging ✅
- [ ] All 14 endpoints have log_event() calls
- [ ] app_version is captured automatically
- [ ] Event types are consistent
- [ ] No sensitive data in logs

---

## Risk Mitigation

### Risk 1: Watermark Obscures Content
**Mitigation:** Use 20% opacity, test on sample reports

### Risk 2: Hash Mismatch
**Mitigation:** Test hash calculation with known PDFs, verify consistency

### Risk 3: Missing Audit Events
**Mitigation:** Create automated test to verify all endpoints log events

---

## Post-Implementation Checklist

- [ ] All code changes committed
- [ ] Migration applied to database
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Regulatory documents updated with implementation details
- [ ] Screenshots captured for evidence
- [ ] Code freeze tag created

---

**END OF IMPLEMENTATION PLAN**
