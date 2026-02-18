# TEST EVIDENCE DIRECTORY

**Purpose:** Store validation and verification test evidence for CDSCO submission

**Document Version:** 1.0  
**Effective Date:** 2026-02-14

---

## DIRECTORY STRUCTURE

```
test_evidence/
├── README.md (this file)
├── pytest_output/
│   ├── full_test_run.txt
│   ├── coverage_report.html
│   └── coverage_summary.txt
├── api_tests/
│   ├── postman_collection.json
│   ├── newman_test_output.txt
│   └── api_test_results.html
├── e2e_tests/
│   ├── assessment_flow_test.log
│   ├── red_flag_detection_test.log
│   └── pdf_generation_test.log
├── validation_tests/
│   ├── invalid_input_rejection.log
│   ├── boundary_value_tests.log
│   └── security_tests.log
└── screenshots/
    ├── draft_report_watermark.png
    ├── reviewed_report.png
    ├── red_flag_display.png
    └── clinical_inbox.png
```

---

## REQUIRED TEST EVIDENCE

### 1. Unit Test Evidence
**File:** `pytest_output/full_test_run.txt`

**Requirements:**
- Full pytest output showing all tests
- Test execution timestamp
- Pass/fail status for each test
- Total test count and pass rate

**Command to Generate:**
```bash
pytest -v --tb=short > regulatory/V1/software_vv/test_evidence/pytest_output/full_test_run.txt
```

---

### 2. Code Coverage Report
**Files:** 
- `pytest_output/coverage_report.html` (detailed)
- `pytest_output/coverage_summary.txt` (summary)

**Requirements:**
- Coverage percentage for each module
- Minimum 80% coverage on critical paths
- 100% coverage on scoring modules

**Command to Generate:**
```bash
pytest --cov=apps.clinical_ops --cov-report=html --cov-report=term > regulatory/V1/software_vv/test_evidence/pytest_output/coverage_summary.txt
mv htmlcov/* regulatory/V1/software_vv/test_evidence/pytest_output/
```

---

### 3. API Test Results
**Files:**
- `api_tests/postman_collection.json` (test definitions)
- `api_tests/newman_test_output.txt` (execution results)

**Requirements:**
- All API endpoints tested
- Valid and invalid input scenarios
- Authentication and authorization tests
- OTP verification tests

**Command to Generate:**
```bash
newman run postman_collection.json > regulatory/V1/software_vv/test_evidence/api_tests/newman_test_output.txt
```

---

### 4. End-to-End Test Logs
**Files:**
- `e2e_tests/assessment_flow_test.log`
- `e2e_tests/red_flag_detection_test.log`
- `e2e_tests/pdf_generation_test.log`

**Requirements:**
- Complete assessment flow (start to PDF download)
- Red flag detection and escalation
- PDF generation with watermark
- Session resume functionality

---

### 5. Validation Test Evidence
**Files:**
- `validation_tests/invalid_input_rejection.log`
- `validation_tests/boundary_value_tests.log`
- `validation_tests/security_tests.log`

**Requirements:**
- Invalid input rejection (out-of-range values)
- Boundary value testing (min, max, edge cases)
- Security testing (cross-org access, expired tokens)
- Duplicate submission prevention

---

### 6. Screenshots
**Files:**
- `screenshots/draft_report_watermark.png`
- `screenshots/reviewed_report.png`
- `screenshots/red_flag_display.png`
- `screenshots/clinical_inbox.png`

**Requirements:**
- Visual evidence of UI states
- Watermark visibility on PROVISIONAL reports
- Red flag highlighting
- Clinical review workflow

---

## TEST EXECUTION CHECKLIST

### Pre-Submission Requirements
- [ ] All unit tests passing (100%)
- [ ] Code coverage ≥80% on critical paths
- [ ] Code coverage 100% on scoring modules
- [ ] All API tests passing
- [ ] E2E assessment flow test passing
- [ ] Red flag detection test passing
- [ ] PDF generation test passing
- [ ] Invalid input rejection test passing
- [ ] Security tests passing
- [ ] Screenshots captured

### Evidence Archive
- [ ] All test outputs saved to this directory
- [ ] Test execution timestamps documented
- [ ] Test environment documented (Python version, Django version)
- [ ] Test data anonymized (no real patient data)

---

## TEST ENVIRONMENT

**Python Version:** 3.11.x  
**Django Version:** 4.2 LTS  
**Database:** PostgreSQL 14.x (test database)  
**Test Framework:** pytest  
**API Testing:** Postman/Newman  
**Coverage Tool:** pytest-cov

---

## REGULATORY TRACEABILITY

Each test file should reference:
- **Requirement ID** (from traceability matrix)
- **Risk ID** (if testing risk mitigation)
- **Test Objective**
- **Expected Result**
- **Actual Result**
- **Pass/Fail Status**

---

## INSTRUCTIONS FOR GENERATING EVIDENCE

### Step 1: Run Unit Tests
```bash
cd neurova_backend
pytest -v --tb=short --cov=apps.clinical_ops --cov-report=html --cov-report=term > regulatory/V1/software_vv/test_evidence/pytest_output/full_test_run.txt
```

### Step 2: Save Coverage Report
```bash
cp -r htmlcov/* regulatory/V1/software_vv/test_evidence/pytest_output/
```

### Step 3: Run API Tests
```bash
newman run postman_collection.json > regulatory/V1/software_vv/test_evidence/api_tests/newman_test_output.txt
```

### Step 4: Run E2E Tests
```bash
# Execute E2E test scripts and redirect output
python manage.py test_assessment_flow > regulatory/V1/software_vv/test_evidence/e2e_tests/assessment_flow_test.log
```

### Step 5: Capture Screenshots
- Manually capture screenshots of UI states
- Save to `screenshots/` directory
- Use descriptive filenames

### Step 6: Archive Evidence
- Verify all files present
- Compress directory for submission
- Include in regulatory package

---

## NOTES

1. **No Real Patient Data:** All test evidence must use anonymized or synthetic data
2. **Timestamps:** All test runs must include execution timestamps
3. **Reproducibility:** Tests should be reproducible with documented test data
4. **Version Control:** Test evidence should match code freeze version (neurova_samd_v1_0_0)

---

## DOCUMENT CONTROL

**Prepared By:** QA / Software Engineering  
**Reviewed By:** [To be completed]  
**Approved By:** [To be completed]  
**Effective Date:** 2026-02-14

---

**END OF README**
