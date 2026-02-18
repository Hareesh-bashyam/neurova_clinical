# RISK MANAGEMENT FILE (ISO 14971)
**Document Version:** 1.0  
**Effective Date:** 2026-02-14  
**Device:** Neurova Clinical Engine V1  
**Standard:** ISO 14971:2019 (Medical Devices - Application of Risk Management)

---

## 1. RISK MANAGEMENT OVERVIEW

### 1.1 Purpose
Systematic identification, evaluation, and mitigation of hazards associated with the Neurova Clinical Engine V1 throughout its lifecycle.

### 1.2 Risk Management Process
1. **Risk Analysis:** Identify hazards and hazardous situations
2. **Risk Evaluation:** Assess severity and probability
3. **Risk Control:** Implement mitigations
4. **Residual Risk Evaluation:** Assess remaining risk
5. **Risk-Benefit Analysis:** Verify acceptable risk level

### 1.3 Risk Acceptability Criteria

**Risk Matrix:**
| Severity | Probability | Risk Level | Acceptable? |
|----------|-------------|------------|-------------|
| Catastrophic | Frequent | CRITICAL | ❌ No |
| Catastrophic | Probable | HIGH | ❌ No |
| Catastrophic | Occasional | MEDIUM | ⚠️ With mitigation |
| Major | Frequent | HIGH | ❌ No |
| Major | Probable | MEDIUM | ⚠️ With mitigation |
| Major | Occasional | LOW | ✅ Yes |
| Moderate | Frequent | MEDIUM | ⚠️ With mitigation |
| Moderate | Probable | LOW | ✅ Yes |
| Minor | Any | LOW | ✅ Yes |

---

## 2. CLINICAL HAZARD SCENARIOS

### HAZARD 001: False Reassurance

**Hazard Description:** Low screening score leads to false reassurance, delaying needed treatment.

**Hazardous Situation:**  
Patient scores in "Minimal" range (PHQ-9: 0-4) but has significant depression not captured by instrument.

**Potential Harm:**
- **Severity:** Major (delayed treatment, worsening condition)
- **Probability:** Occasional (screening tools have known sensitivity limitations)
- **Initial Risk:** MEDIUM

**Root Causes:**
- Instrument sensitivity <100%
- Patient underreporting symptoms
- Atypical presentation not captured by standardized questions

**Mitigation Measures:**
1. **Disclaimer:** "Screening Summary – Not a Diagnosis" on all outputs
2. **IFU Guidance:** Instructs clinicians to use clinical judgment beyond scores
3. **Professional Review:** All outputs require clinician interpretation
4. **Labeling:** Clear statement that screening is not diagnostic

**Implementation References:**
- **Document:** `/regulatory/V1/intended_use/INTENDED_USE.md`
- **Code:** PDF disclaimer template
- **UI:** Header disclaimer on all result screens

**Residual Risk:**
- **Severity:** Major
- **Probability:** Remote (with professional oversight)
- **Residual Risk Level:** LOW
- **Acceptable:** ✅ Yes (benefit outweighs risk with mitigations)

---

### HAZARD 002: Delayed Review of Critical Findings

**Hazard Description:** Red flag (suicidal ideation) not reviewed promptly by clinician.

**Hazardous Situation:**  
Patient endorses PHQ-9 Q9 (suicidal ideation), but report sits in PROVISIONAL status without clinician review for extended period.

**Potential Harm:**
- **Severity:** Catastrophic (suicide attempt, death)
- **Probability:** Occasional
- **Initial Risk:** HIGH

**Root Causes:**
- Clinician workload/delays
- Notification failure
- Lack of urgency awareness

**Mitigation Measures:**
1. **Automatic Flagging:** PHQ-9 Q9 ≥1 triggers CRITICAL flag
2. **Status Enforcement:** Critical flags default to PROVISIONAL (cannot auto-promote)
3. **Watermark:** "PROVISIONAL – NOT CLINICALLY REVIEWED" applied
4. **Audit Logging:** All red flags logged with timestamp
5. **IFU Instruction:** Red flags require immediate clinical attention

**Implementation References:**
- **Code:** `/apps/clinical_ops/scoring/phq9.py` - Red flag detection
- **Code:** `/apps/clinical_ops/services/signoff_engine.py` - Status enforcement
- **Database:** `ClinicalAuditEvent` - Red flag logging
- **PDF:** Watermark application logic

**Residual Risk:**
- **Severity:** Catastrophic
- **Probability:** Remote (with immediate flagging and watermarking)
- **Residual Risk Level:** MEDIUM
- **Acceptable:** ✅ Yes (maximum feasible mitigation implemented)

**Additional Controls (Post-Market):**
- Monitor average time-to-review for flagged reports
- User feedback on notification effectiveness

---

### HAZARD 003: Red Flag Ignored by Clinician

**Hazard Description:** Clinician reviews report but fails to act on red flag.

**Hazardous Situation:**  
Clinician marks report as REVIEWED without addressing suicidal ideation flag.

**Potential Harm:**
- **Severity:** Catastrophic (suicide attempt, death)
- **Probability:** Remote
- **Initial Risk:** MEDIUM

**Root Causes:**
- Clinician oversight
- Flag not visually prominent
- Clinician fatigue/distraction

**Mitigation Measures:**
1. **Visual Highlighting:** Red flags displayed in red, bold text
2. **Separate Section:** Red flags in dedicated "Critical Findings" section
3. **IFU Training:** Emphasizes red flag review requirement
4. **Audit Trail:** Clinician review logged (accountability)

**Implementation References:**
- **Code:** PDF template - Red flag formatting
- **UI:** Critical findings section styling
- **Database:** `ClinicalAuditEvent.REPORT_REVIEWED` - Review logging

**Residual Risk:**
- **Severity:** Catastrophic
- **Probability:** Rare (with visual prominence and training)
- **Residual Risk Level:** MEDIUM
- **Acceptable:** ✅ Yes (clinician responsibility, device provides maximum support)

---

### HAZARD 004: Misinterpretation of Severity Bands

**Hazard ID:** HAZ-004  
**Hazard Category:** Clinical Misuse

**Hazard Description:** Clinician or patient interprets severity band labels (e.g., "Moderate Depression") as diagnostic conclusion.

**Hazardous Situation:**  
Clinician uses severity band (e.g., "Moderate Depression" for PHQ-9 score 10-14) as diagnosis without comprehensive clinical assessment, leading to inappropriate treatment decisions.

**Potential Harm:**
- Inappropriate treatment (over-treatment or under-treatment)
- Missed comorbidities or differential diagnoses
- Patient receives treatment not suited to actual condition
- **Severity:** MODERATE (inappropriate treatment, suboptimal outcomes)
- **Probability:** Occasional (time pressure, lack of training)
- **Initial Risk:** MEDIUM

**Root Causes:**
- Ambiguous labeling that resembles diagnostic language
- Lack of user training on screening vs. diagnosis
- Time pressure on clinicians to make quick decisions
- Severity band labels sound diagnostic ("Moderate Depression")

**Mitigation Measures:**

1. **Labeling (Primary Control):**
   - Header: "Screening Summary" (not "Diagnostic Report")
   - Severity bands prefixed with "Screening Severity:" 
   - Example: "Screening Severity: Moderate" (not "Diagnosis: Moderate Depression")
   - Disclaimer on every page: "This is a screening tool, not a diagnostic instrument"

2. **Workflow Control:**
   - All outputs require professional interpretation
   - IFU explicitly states: "Results must be integrated with clinical judgment"
   - User qualifications specified (licensed mental health professionals only)

3. **Code Implementation:**
   - **File:** PDF header template
   - **File:** Severity band display logic
   - **File:** `/regulatory/V1/ifu_v1.md` - Section 3: Screening vs. Diagnosis

**Verification:**
- ✅ Text search: No diagnostic language in code/UI
- ✅ Document review: Disclaimers present on all PDFs
- ✅ User testing: Clinicians understand limitations

**Residual Risk Assessment:**
- **Residual Severity:** MODERATE
- **Residual Probability:** Remote (with clear labeling and training)
- **Residual Risk Level:** LOW
- **Acceptable:** ✅ Yes (benefit outweighs risk)

**Justification:** Device provides maximum feasible labeling clarity. Residual risk is clinician responsibility to use clinical judgment, which is standard of care.

---

### HAZARD 005: Alarm Fatigue

**Hazard ID:** HAZ-005  
**Hazard Category:** Clinical Workflow

**Hazard Description:** Excessive red flag alerts lead to clinician desensitization, causing critical findings to be overlooked.

**Hazardous Situation:**  
System flags too many reports as "PROVISIONAL" or "CRITICAL," causing clinicians to become desensitized to alerts. A genuinely critical case (PHQ-9 Q9 = 3, active suicidal ideation) is dismissed as "another false alarm."

**Potential Harm:**
- Missed critical red flags (suicidal ideation, severe anxiety)
- Delayed intervention for high-risk patients
- Patient harm or death
- **Severity:** CATASTROPHIC (suicide attempt, death)
- **Probability:** Occasional (if alert threshold too low)
- **Initial Risk:** HIGH

**Root Causes:**
- Overly sensitive red flag criteria
- High false-positive rate
- Lack of severity stratification in alerts
- Clinician workload and time pressure

**Mitigation Measures:**

1. **Code (Primary Control):**
   - **Conservative Red Flag Criteria:** Only truly critical responses trigger flags
     - PHQ-9 Q9 ≥ 1 (suicidal ideation)
     - GAD-7 total ≥ 15 (severe anxiety)
   - **No false positives:** Moderate scores do NOT trigger critical alerts
   - **File:** `/apps/clinical_ops/scoring/phq9.py` (lines 45-67)
   - **File:** `/apps/clinical_ops/scoring/gad7.py`

2. **Workflow Control:**
   - Two-tier alert system:
     - **CRITICAL:** Requires immediate attention (red flags)
     - **PROVISIONAL:** Awaiting routine review (no red flags)
   - **File:** `/apps/clinical_ops/services/signoff_engine.py`

3. **Labeling:**
   - IFU Section 5: "Red Flag Escalation Procedures"
   - Clear definition of what constitutes a red flag
   - Expected red flag frequency: <10% of screenings

**Verification:**
- ✅ Test: Red flag rate in pilot data <10%
- ✅ Literature review: Criteria match clinical guidelines
- ✅ User feedback: Alerts perceived as appropriate

**Residual Risk Assessment:**
- **Residual Severity:** CATASTROPHIC
- **Residual Probability:** Rare (with conservative criteria)
- **Residual Risk Level:** MEDIUM
- **Acceptable:** ✅ Yes (maximum feasible mitigation)

**Post-Market Monitoring:**
- Track red flag frequency quarterly
- Alert if red flag rate >15% (indicates over-flagging)
- User feedback on alert appropriateness

---

### HAZARD 006: Patient Self-Interpretation Without Consultation

**Hazard ID:** HAZ-006  
**Hazard Category:** Misuse

**Hazard Description:** Patient accesses screening report directly and interprets results without professional consultation, leading to inappropriate self-treatment or distress.

**Hazardous Situation:**  
Patient receives report link, views "Moderate Depression" severity band, and either:
1. Self-diagnoses and seeks inappropriate treatment (e.g., online medication)
2. Experiences severe distress from label without professional support
3. Dismisses results as "not that bad" and avoids needed care

**Potential Harm:**
- Inappropriate self-treatment
- Severe psychological distress
- Delayed professional care
- Self-harm or suicide (if distressed by results)
- **Severity:** MAJOR (inappropriate treatment, psychological harm)
- **Probability:** Probable (patients naturally curious about results)
- **Initial Risk:** HIGH

**Root Causes:**
- Patient access to report without clinician present
- Lack of patient education on interpretation
- Report language not patient-friendly
- No gatekeeper for report access

**Mitigation Measures:**

1. **Workflow (Primary Control):**
   - **Controlled Distribution:** Reports delivered to clinicians only, not patients
   - **Clinician Gatekeeper:** Clinician decides if/when to share with patient
   - **IFU Guidance:** Section 7: "Report Distribution and Patient Communication"
   - Recommends clinician review results with patient in consultation

2. **Labeling:**
   - Report header: "FOR PROFESSIONAL USE ONLY"
   - Disclaimer: "This report is intended for licensed mental health professionals"
   - Patient-facing materials: Separate, simplified summary (if provided)

3. **Code:**
   - **File:** `/apps/clinical_ops/api/v1/report_download_views.py`
   - OTP verification ensures only authorized clinicians access reports
   - No direct patient access to PDF reports

**Verification:**
- ✅ Access control test: Patients cannot access reports without OTP
- ✅ IFU review: Clear guidance on report distribution
- ✅ User training: Clinicians understand distribution policy

**Residual Risk Assessment:**
- **Residual Severity:** MAJOR
- **Residual Probability:** Remote (with controlled distribution)
- **Residual Risk Level:** LOW
- **Acceptable:** ✅ Yes

**Justification:** Device is intended for professional use only. Clinician is responsible for appropriate patient communication, which is standard of care.

---

### HAZARD 007: Report Not Reviewed But Assumed Reviewed

**Hazard ID:** HAZ-007  
**Hazard Category:** Workflow Error

**Hazard Description:** Report remains in PROVISIONAL status but clinician assumes it has been reviewed, leading to delayed action on critical findings.

**Hazardous Situation:**  
1. Screening completed, report generated with PROVISIONAL status
2. Clinician assumes another team member reviewed it
3. Report sits unreviewed for days/weeks
4. Critical red flag (suicidal ideation) not addressed
5. Patient harm occurs

**Potential Harm:**
- Delayed intervention for critical findings
- Patient deterioration
- Suicide attempt or death
- **Severity:** CATASTROPHIC (suicide, death)
- **Probability:** Occasional (communication failures in teams)
- **Initial Risk:** HIGH

**Root Causes:**
- Unclear responsibility for review
- Poor team communication
- Status not visually prominent
- Assumption that "generated" = "reviewed"

**Mitigation Measures:**

1. **Code (Primary Control):**
   - **Watermarking System:** PROVISIONAL reports display:
     - "PROVISIONAL – NOT CLINICALLY REVIEWED"
     - Watermark appears diagonally across all pages
     - Red text, 60pt font, 20% opacity
   - **File:** `/apps/clinical_ops/pdf/watermark.py`
   - **Visual Test:** Watermark clearly visible

2. **Workflow:**
   - **Status Enforcement:** Reports cannot transition from PROVISIONAL to REVIEWED without explicit clinician action
   - **Audit Trail:** Review action logged with clinician ID and timestamp
   - **File:** `/apps/clinical_ops/services/signoff_engine.py`

3. **Labeling:**
   - IFU Section 6: "Report Status and Review Requirements"
   - Clear explanation of DRAFT/PROVISIONAL/REVIEWED statuses
   - PROVISIONAL = "Awaiting clinical review"

**Verification:**
- ✅ Visual test: Watermark visible on PROVISIONAL reports
- ✅ Visual test: Watermark absent on REVIEWED reports
- ✅ Workflow test: Status cannot auto-transition
- ✅ Audit test: Review actions logged

**Residual Risk Assessment:**
- **Residual Severity:** CATASTROPHIC
- **Residual Probability:** Rare (with watermarking)
- **Residual Risk Level:** MEDIUM
- **Acceptable:** ✅ Yes (maximum feasible mitigation)

**Justification:** Watermarking provides maximum visual indication of review status. Residual risk is organizational responsibility to establish clear review workflows.

---

### HAZARD 008: Internet Failure Causing Delay

**Hazard ID:** HAZ-008  
**Hazard Category:** Technical Infrastructure

**Hazard Description:** Internet connectivity failure prevents timely completion of screening or access to results, delaying clinical care.

**Hazardous Situation:**  
1. **Scenario A:** Patient starts screening, internet fails mid-session, cannot complete
2. **Scenario B:** Screening completed, but clinician cannot access report due to internet outage
3. **Scenario C:** Critical red flag detected, but notification email cannot be sent due to internet failure

**Potential Harm:**
- Delayed screening completion
- Delayed access to critical findings
- Delayed intervention for high-risk patients
- **Severity:** MODERATE (delay in care, but not complete failure)
- **Probability:** Occasional (internet outages occur)
- **Initial Risk:** MEDIUM

**Root Causes:**
- Network infrastructure failures
- ISP outages
- Server connectivity issues
- Patient location with poor connectivity

**Mitigation Measures:**

1. **Code (Primary Control):**
   - **Session Resume Logic:**
     - Responses auto-saved after each question
     - Patient can resume from last saved question when connectivity restored
     - **File:** `/apps/clinical_ops/services/public_token_validator.py`
     - **File:** Session management logic
   
   - **Offline Fallback:**
     - Local storage caches responses before server sync
     - **File:** Frontend local storage implementation
   
   - **Retry Logic:**
     - Automatic retry with exponential backoff (1s, 2s, 4s)
     - **File:** API request retry logic

2. **Workflow:**
   - **Extended Token Validity:** 24-hour token expiry allows resume after outage
   - **Manual Retry:** User can manually retry failed operations
   - **Support Access:** Support team can manually retrieve data if needed

3. **Labeling:**
   - IFU Section 8: "Network Requirements and Troubleshooting"
   - Minimum bandwidth: 1 Mbps
   - Recommended: Stable internet connection
   - Troubleshooting steps for connectivity issues

**Verification:**
- ✅ Test: Disconnect network mid-screening → Resume successful
- ✅ Test: Network timeout → Automatic retry successful
- ✅ Test: Extended outage → Session resume after 2 hours successful

**Residual Risk Assessment:**
- **Residual Severity:** MODERATE
- **Residual Probability:** Remote (with auto-save and resume)
- **Residual Risk Level:** LOW
- **Acceptable:** ✅ Yes

**Justification:** Session resume and auto-save minimize data loss. Extended outages are rare and outside device control. Residual risk is acceptable given benefits of remote screening capability.

**Post-Market Monitoring:**
- Track abandonment rate due to connectivity issues
- Monitor average time to resume after interruption
- User feedback on connectivity experience

---

### HAZARD 009: Calculation Error (Incorrect Score)


### HAZARD 009: Calculation Error (Incorrect Score)

**Hazard ID:** HAZ-009  
**Hazard Category:** Software/Technical

**Hazard Description:** Software bug causes incorrect score calculation.

**Hazardous Situation:**  
PHQ-9 score calculated as 8 when true score is 18, missing severe depression.

**Potential Harm:**
- **Severity:** Major (delayed treatment)
- **Probability:** Remote (with testing)
- **Initial Risk:** MEDIUM

**Root Causes:**
- Coding error
- Untested edge case
- Data type mismatch

**Mitigation Measures:**
1. **Deterministic Logic:** No randomness, pure calculation
2. **Unit Testing:** Comprehensive test coverage for all scoring functions
3. **Literature Validation:** Scores compared to published examples
4. **Code Review:** All scoring logic peer-reviewed
5. **Regression Testing:** Changes verified against baseline

**Implementation References:**
- **Code:** `/apps/clinical_ops/scoring/` - All scoring modules
- **Tests:** `/tests/scoring/test_phq9.py`, `/tests/scoring/test_gad7.py`
- **CI/CD:** Automated test execution on every commit

**Verification:**
- ✅ 100% test coverage on scoring functions
- ✅ Edge cases tested (min, max, boundary values)
- ✅ Literature examples verified

**Residual Risk Assessment:**
- **Residual Severity:** Major
- **Residual Probability:** Rare (with comprehensive testing)
- **Residual Risk Level:** LOW
- **Acceptable:** ✅ Yes

---

### HAZARD 010: Data Loss (Network Interruption)

**Hazard ID:** HAZ-010  
**Hazard Category:** Technical Infrastructure

**Hazard Description:** Patient responses lost due to network failure.

**Hazardous Situation:**  
Patient completes 8 of 9 PHQ-9 questions, network disconnects, responses lost, patient must restart.

**Potential Harm:**
- **Severity:** Minor (inconvenience, potential abandonment)
- **Probability:** Occasional
- **Initial Risk:** LOW

**Root Causes:**
- Network instability
- Server timeout
- Client-side storage failure

**Mitigation Measures:**
1. **Auto-Save:** Responses saved after each question
2. **Session Resume:** Patient can resume from last saved question
3. **Local Storage:** Temporary client-side storage before server sync
4. **Audit Logging:** Abandonment tracked for monitoring

**Implementation References:**
- **Code:** Session management logic
- **Database:** `Order` model with partial completion tracking
- **Frontend:** Local storage implementation

**Residual Risk Assessment:**
- **Residual Severity:** Minor
- **Residual Probability:** Remote (with auto-save)
- **Residual Risk Level:** MINIMAL
- **Acceptable:** ✅ Yes

---

### HAZARD 011: Duplicate Report Generation

**Hazard ID:** HAZ-011  
**Hazard Category:** Software/Technical

**Hazard Description:** Same screening data generates multiple reports, causing confusion.

**Hazardous Situation:**  
Clinician downloads report twice, receives two different PDFs with different timestamps, unsure which is authoritative.

**Potential Harm:**
- **Severity:** Moderate (confusion, potential use of wrong version)
- **Probability:** Occasional
- **Initial Risk:** MEDIUM

**Root Causes:**
- No unique constraint on reports
- Concurrent requests
- User error (multiple clicks)

**Mitigation Measures:**
1. **Unique Constraint:** Database prevents duplicate reports per order
2. **Idempotency:** Repeated requests return same report
3. **Version Control:** Report version tracked in database
4. **Audit Logging:** All report generation logged

**Implementation References:**
- **Database:** Unique constraint on `(order_id, report_version)`
- **Code:** Idempotent report generation logic
- **Audit:** `PDF_EXPORTED` event logging

**Residual Risk Assessment:**
- **Residual Severity:** Moderate
- **Residual Probability:** Rare (with unique constraint)
- **Residual Risk Level:** LOW
- **Acceptable:** ✅ Yes

---

### HAZARD 012: PDF Generation Failure

**Hazard ID:** HAZ-012  
**Hazard Category:** Software/Technical

**Hazard Description:** PDF generation fails, clinician cannot access report.

**Hazardous Situation:**  
Screening completed, but PDF generation crashes due to overflow or rendering error.

**Potential Harm:**
- **Severity:** Moderate (delayed access to results)
- **Probability:** Occasional
- **Initial Risk:** MEDIUM

**Root Causes:**
- Text overflow in PDF template
- Missing data fields
- ReportLab library bug

**Mitigation Measures:**
1. **Overflow Validation:** Text truncation with ellipsis if exceeds space
2. **Error Logging:** All PDF failures logged with stack trace
3. **Fallback:** Raw data export available if PDF fails
4. **Testing:** PDF generation tested with edge cases (long text, special characters)

**Implementation References:**
- **Code:** PDF generation error handling
- **Logging:** PDF failure logging
- **Tests:** PDF edge case tests

**Residual Risk Assessment:**
- **Residual Severity:** Moderate
- **Residual Probability:** Remote (with validation and testing)
- **Residual Risk Level:** LOW
- **Acceptable:** ✅ Yes

---

### HAZARD 013: Database Outage

**Hazard ID:** HAZ-013  
**Hazard Category:** Technical Infrastructure

**Hazard Description:** Database unavailable, system cannot save or retrieve data.

**Hazardous Situation:**  
Patient completes screening, but responses cannot be saved due to database outage.

**Potential Harm:**
- **Severity:** Moderate (data loss, patient must re-complete)
- **Probability:** Remote
- **Initial Risk:** LOW

**Root Causes:**
- Database server failure
- Network partition
- Maintenance downtime

**Mitigation Measures:**
1. **Atomic Transactions:** All-or-nothing saves (no partial data)
2. **Error Messaging:** Clear user notification of save failure
3. **Retry Logic:** Automatic retry with exponential backoff
4. **Infrastructure:** Database redundancy and backups

**Implementation References:**
- **Code:** Database transaction management
- **Infrastructure:** PostgreSQL replication
- **Monitoring:** Database health monitoring

**Residual Risk Assessment:**
- **Residual Severity:** Moderate
- **Residual Probability:** Rare (with infrastructure redundancy)
- **Residual Risk Level:** LOW
- **Acceptable:** ✅ Yes

---

## 4. SECURITY/PRIVACY HAZARDS

### HAZARD 014: Unauthorized Report Access

**Hazard ID:** HAZ-014  
**Hazard Category:** Security/Privacy

**Hazard Description:** Unauthorized individual accesses patient screening report.

**Hazardous Situation:**  
Report link shared or intercepted, non-clinician views sensitive mental health data.

**Potential Harm:**
- **Severity:** Major (privacy breach, patient distress)
- **Probability:** Occasional
- **Initial Risk:** MEDIUM

**Root Causes:**
- Weak access controls
- Link sharing
- Token leakage

**Mitigation Measures:**
1. **OTP Protection:** Report download requires one-time password
2. **Token Expiration:** Access tokens expire after 24 hours
3. **Audit Logging:** All access attempts logged
4. **HTTPS:** Encrypted data transmission

**Implementation References:**
- **Code:** `/apps/clinical_ops/api/v1/report_download_views.py` - OTP verification
- **Database:** Token expiration logic
- **Audit:** `PDF_EXPORTED` event with user tracking

**Residual Risk Assessment:**
- **Residual Severity:** Major
- **Residual Probability:** Rare (with OTP and expiration)
- **Residual Risk Level:** LOW
- **Acceptable:** ✅ Yes

---

## 5. RISK-BENEFIT ANALYSIS

### 5.1 Benefits
- **Efficiency:** Faster screening compared to paper
- **Standardization:** Consistent scoring, no manual calculation errors
- **Red Flag Detection:** Automatic identification of high-risk responses
- **Audit Trail:** Complete record of screening and review
- **Accessibility:** Remote screening capability

### 5.2 Residual Risks Summary

| Hazard ID | Hazard Description | Initial Risk | Residual Risk | Acceptable? |
|-----------|-------------------|--------------|---------------|-------------|
| HAZ-001 | False Reassurance | MEDIUM | LOW | ✅ Yes |
| HAZ-002 | Delayed Review of Critical Findings | HIGH | MEDIUM | ✅ Yes (max mitigation) |
| HAZ-003 | Red Flag Ignored by Clinician | MEDIUM | MEDIUM | ✅ Yes (clinician responsibility) |
| HAZ-004 | Misinterpretation of Severity Bands | MEDIUM | LOW | ✅ Yes |
| HAZ-005 | Alarm Fatigue | HIGH | MEDIUM | ✅ Yes (max mitigation) |
| HAZ-006 | Patient Self-Interpretation | HIGH | LOW | ✅ Yes |
| HAZ-007 | Report Not Reviewed But Assumed Reviewed | HIGH | MEDIUM | ✅ Yes (max mitigation) |
| HAZ-008 | Internet Failure Causing Delay | MEDIUM | LOW | ✅ Yes |
| HAZ-009 | Calculation Error | MEDIUM | LOW | ✅ Yes |
| HAZ-010 | Data Loss (Network Interruption) | LOW | MINIMAL | ✅ Yes |
| HAZ-011 | Duplicate Report Generation | MEDIUM | LOW | ✅ Yes |
| HAZ-012 | PDF Generation Failure | MEDIUM | LOW | ✅ Yes |
| HAZ-013 | Database Outage | LOW | LOW | ✅ Yes |
| HAZ-014 | Unauthorized Report Access | MEDIUM | LOW | ✅ Yes |

### 5.3 Overall Risk-Benefit Conclusion
The **benefits outweigh the residual risks**. All identified hazards have been mitigated to acceptable levels through:
- Technical controls (OTP, watermarking, red flag detection, session resume)
- Procedural controls (professional review requirement, controlled distribution)
- Informational controls (disclaimers, IFU, training)

**Critical Hazards (MEDIUM Residual Risk):**
- HAZ-002: Delayed Review - Mitigated by watermarking and status enforcement
- HAZ-003: Red Flag Ignored - Mitigated by visual prominence and training
- HAZ-005: Alarm Fatigue - Mitigated by conservative red flag criteria
- HAZ-007: Assumed Reviewed - Mitigated by watermarking system

All MEDIUM residual risks are at maximum feasible mitigation and are acceptable given the clinical benefits of the device.


---

## 6. POST-MARKET RISK MONITORING

### 6.1 Ongoing Surveillance
- **Red Flag Frequency:** Monitor for unexpected patterns
- **Incident Reports:** Track user-reported issues
- **Audit Log Analysis:** Identify anomalies (e.g., high abandonment)
- **User Feedback:** Collect safety-related feedback

### 6.2 Risk Re-Evaluation Triggers
- New hazard identified
- Incident or near-miss reported
- Scope change or new feature
- Annual review

---

## DOCUMENT CONTROL

**Prepared By:** Risk Management / Regulatory Affairs  
**Reviewed By:** [To be completed]  
**Approved By:** [To be completed]  
**Effective Date:** 2026-02-14  
**Next Review:** 2027-02-14

---

**END OF DOCUMENT**
