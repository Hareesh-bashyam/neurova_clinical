# SCOPE DEFINITION – NEUROVA CLINICAL ENGINE V1
**Document Version:** 1.0  
**Effective Date:** 2026-02-14  
**Regulatory Status:** LOCKED  
**Purpose:** Define and freeze feature scope to prevent classification drift

---

## 1. VERSION CONTROL

### 1.1 Application Version
- **Current Version:** 1.0
- **Version Storage:** Database field `APP_VERSION`
- **Version Format:** Semantic versioning (MAJOR.MINOR.PATCH)

### 1.2 Component Versioning
All clinical components must maintain version tracking:
- **Battery Version:** Stored per order in `battery_version` field
- **Consent Version:** Stored per order in `consent_version` field
- **Instrument Version:** Each psychometric instrument tracks version independently

---

## 2. INCLUDED FEATURES (IN SCOPE FOR V1)

### 2.1 Core Screening Functionality
✅ **Digitized Screening Batteries**
- PHQ-9 (Patient Health Questionnaire - Depression)
- GAD-7 (Generalized Anxiety Disorder)
- Additional validated psychometric instruments
- Digital administration with session resume capability
- Progress tracking and completion validation

✅ **Automated Scoring**
- Deterministic calculation based on validated algorithms
- Severity band classification per published literature
- Score summation and subscale calculations
- Exact match to paper-based scoring methods

✅ **Red Flag Detection**
- Critical response identification (e.g., suicidal ideation)
- Automatic flagging of high-risk responses
- Mandatory hold state for critical flags
- Escalation workflow triggers

✅ **Audit Logging**
- Comprehensive event tracking
- User action logging
- Consent capture and versioning
- PDF export tracking
- Clinical review tracking
- Deletion request logging

✅ **Structured Reporting**
- PDF generation with standardized format
- Screening summary presentation
- Mandatory disclaimers on all outputs
- Watermarking for provisional status
- OTP-secured report access

✅ **Clinical Workflow Support**
- Order creation and management
- Patient consent workflow
- Clinician review interface
- Status progression (DRAFT → PROVISIONAL → REVIEWED)
- Report download and export

---

## 3. EXPLICITLY EXCLUDED FEATURES (OUT OF SCOPE FOR V1)

> [!CAUTION]
> **The following features are PROHIBITED in V1 to maintain device classification:**

### 3.1 AI/ML Prediction Features
❌ **Facial Emotion Detection**
- No computer vision analysis
- No emotion recognition algorithms
- No behavioral pattern detection from video/images

❌ **AI-Based Prediction**
- No machine learning models for outcome prediction
- No risk stratification beyond validated scoring
- No predictive analytics for treatment response
- No automated diagnosis suggestions

❌ **Natural Language Processing**
- No free-text analysis of patient responses
- No sentiment analysis
- No automated interpretation of narrative content

### 3.2 Clinical Decision Support
❌ **Medication Suggestions**
- No drug recommendations
- No dosage calculations
- No medication interaction checking
- No pharmacological guidance

❌ **Treatment Planning**
- No therapy recommendations
- No treatment pathway suggestions
- No automated care plans
- No intervention recommendations

❌ **Autonomous Diagnosis**
- No diagnostic conclusions
- No condition identification
- No differential diagnosis generation
- No clinical interpretation without human review

### 3.3 Advanced Analytics
❌ **Longitudinal Tracking**
- No trend analysis across multiple screenings
- No progress monitoring dashboards
- No outcome prediction over time

❌ **Population Analytics**
- No aggregated risk scoring
- No cohort analysis
- No epidemiological modeling

### 3.4 Integration Features
❌ **EHR Auto-Population**
- No automatic writing to external medical records
- No bidirectional EHR sync
- No automated clinical note generation

❌ **Direct Patient Communication**
- No automated patient messaging
- No crisis intervention chatbots
- No patient-facing recommendations

---

## 4. SCOPE FREEZE RATIONALE

### 4.1 Why Scope is Locked
Adding features from the excluded list would:
- **Change device classification** from screening tool to diagnostic/treatment device
- **Increase regulatory risk** requiring additional clinical validation
- **Trigger re-submission** to regulatory authorities
- **Extend time-to-market** significantly
- **Increase liability exposure**

### 4.2 Change Control Process
Any proposed feature addition must:
1. **Regulatory Review:** Assess impact on device classification
2. **Clinical Evaluation:** Determine if additional validation required
3. **Risk Assessment:** Update risk management file
4. **Version Increment:** Trigger new regulatory submission if needed
5. **Approval Required:** Executive and regulatory sign-off

---

## 5. SYSTEM IMPLEMENTATION REQUIREMENTS

### 5.1 Version Storage (Database)
```sql
-- Application version tracking
APP_VERSION = "1.0"

-- Per-order versioning
Order.battery_version  -- e.g., "PHQ9_v2.1"
Order.consent_version  -- e.g., "CONSENT_v1.0"
Order.app_version      -- e.g., "1.0"
```

### 5.2 Version Display Requirements
- **PDF Reports:** Must include version string in footer
- **UI Footer:** Display current application version
- **API Responses:** Include version in metadata
- **Audit Logs:** Record version with each event

### 5.3 Feature Flags (Prohibited)
> [!WARNING]
> Feature flags for excluded features are PROHIBITED. Do not implement:
> - Hidden AI/ML models
> - Disabled treatment recommendation logic
> - Commented-out diagnostic code

All excluded features must remain completely absent from codebase.

---

## 6. BOUNDARY ENFORCEMENT

### 6.1 Code Review Checklist
Before any code merge, verify:
- [ ] No diagnostic language in UI or outputs
- [ ] No treatment recommendations
- [ ] No AI/ML model imports or calls
- [ ] No medication databases or drug references
- [ ] No autonomous clinical decision logic
- [ ] Version strings properly updated

### 6.2 Automated Checks
Implement CI/CD checks for:
- Prohibited library imports (e.g., TensorFlow, PyTorch for ML)
- Prohibited keywords in user-facing text
- Version consistency across components

---

## 7. FEATURE COMPARISON TABLE

| Feature Category | V1 Status | Rationale |
|-----------------|-----------|-----------|
| Digitized screening batteries | ✅ Included | Core intended use |
| Automated scoring (validated) | ✅ Included | Deterministic, literature-based |
| Red flag detection | ✅ Included | Safety requirement |
| Audit logging | ✅ Included | Regulatory requirement |
| PDF report generation | ✅ Included | Clinical workflow support |
| Facial emotion detection | ❌ Excluded | Changes classification to AI/ML device |
| AI outcome prediction | ❌ Excluded | Requires extensive clinical validation |
| Medication suggestions | ❌ Excluded | Moves into treatment domain |
| Automated diagnosis | ❌ Excluded | Violates intended use boundary |
| Treatment planning | ❌ Excluded | Outside screening scope |

---

## 8. VALIDATION REQUIREMENTS

### 8.1 Version Verification
Test cases must verify:
- ✅ Version string stored correctly in database
- ✅ Version displayed on all PDFs
- ✅ Version logged in audit events
- ✅ Battery version captured per order
- ✅ Consent version captured per order

### 8.2 Scope Compliance Testing
- ✅ No excluded features accessible via UI
- ✅ No excluded features in API endpoints
- ✅ No prohibited language in outputs
- ✅ All outputs labeled as "Screening Summary"

---

## 9. TRACEABILITY

### 9.1 Requirements Mapping
| Requirement ID | Description | Implementation |
|----------------|-------------|----------------|
| SCOPE-001 | Store app version in database | `settings.APP_VERSION` |
| SCOPE-002 | Store battery version per order | `Order.battery_version` field |
| SCOPE-003 | Store consent version per order | `Order.consent_version` field |
| SCOPE-004 | Display version on PDFs | PDF footer template |
| SCOPE-005 | Exclude AI/ML features | No ML libraries in requirements.txt |

---

## 10. DOCUMENT CONTROL

**Document Owner:** Regulatory Affairs  
**Reviewed By:** [To be completed]  
**Approved By:** [To be completed]  
**Effective Date:** 2026-02-14  
**Next Review:** 2027-02-14 or upon scope change request

---

**END OF DOCUMENT**
