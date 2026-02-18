# POST-MARKET SURVEILLANCE (PMS) PLAN
**Document Version:** 1.0  
**Effective Date:** 2026-02-14  
**Device:** Neurova Clinical Engine V1  
**Regulatory Requirement:** Medical Device Rules (CDSCO), ISO 13485

---

## 1. PMS OVERVIEW

### 1.1 Purpose
Systematically collect and analyze data on device performance and safety after market release to:
- Detect emerging safety issues
- Verify clinical performance in real-world use
- Identify opportunities for improvement
- Fulfill regulatory obligations

### 1.2 Scope
- All installations of Neurova Clinical Engine V1
- All users (clinicians and patients)
- All screening sessions and reports
- All incidents and complaints

---

## 2. DATA COLLECTION METHODS

### 2.1 Automated Metrics (System Logs)

**Frequency:** Continuous collection, quarterly analysis

**Metrics Collected:**
| Metric | Purpose | Target/Threshold |
|--------|---------|------------------|
| Total screenings completed | Usage volume | N/A (baseline) |
| Session abandonment rate | Usability issue indicator | <10% |
| Average completion time (PHQ-9) | Usability baseline | 4.2 min ± 1 min |
| Red flag frequency (PHQ-9 Q9) | Safety monitoring | Baseline TBD |
| Red flag frequency (other) | Safety monitoring | Baseline TBD |
| PDF generation failure rate | Technical issue | <1% |
| OTP verification failure rate | Security/usability | <5% |
| Average time-to-clinician-review | Safety (delayed review risk) | <24 hours for CRITICAL flags |
| Database transaction failures | Data integrity | <0.1% |

**Data Source:** `ClinicalAuditEvent` table, application logs

---

### 2.2 User Feedback Sampling

**Frequency:** Quarterly  
**Sample Size:** Minimum 10% of active users per quarter

**Collection Method:**
- Email survey to clinicians
- Optional patient feedback form at screening completion
- Structured interview with select users

**Questions:**
1. **Usability:** Any difficulties using the system?
2. **Safety:** Any concerns about accuracy or safety?
3. **Performance:** Does the system perform as expected?
4. **Suggestions:** Improvements or new features desired?

**Analysis:** Categorize feedback by theme, prioritize safety-related issues

---

### 2.3 Incident Reporting Mechanism

**Availability:** 24/7 via email and web form

**Incident Categories:**
- **Critical:** Patient harm, data loss, security breach
- **Major:** System unavailable, incorrect score, red flag missed
- **Minor:** Usability issue, cosmetic bug, performance degradation

**Reporting Requirements:**
- **Critical:** Report to regulatory authority within 24 hours
- **Major:** Investigate within 48 hours, report if required
- **Minor:** Log and review quarterly

**Incident Report Contents:**
- Date/time of incident
- User description of event
- Device version
- Patient impact (if any)
- Root cause analysis
- Corrective action taken

---

## 3. SAFETY MONITORING

### 3.1 Red Flag Frequency Monitoring

**Objective:** Detect unexpected patterns in high-risk responses

**Baseline Establishment:**
- First 6 months: Collect data to establish baseline frequency
- Expected PHQ-9 Q9 positive rate: ~10-15% (literature estimate)

**Monitoring:**
- **Quarterly Review:** Compare current quarter to baseline
- **Alert Threshold:** >50% increase from baseline triggers investigation
- **Analysis:** Determine if increase is:
  - Real (population change)
  - Artifact (scoring bug, UI issue)
  - Seasonal variation

**Action:**
- If real: No device action, inform users
- If artifact: Immediate investigation and fix
- If unclear: Enhanced monitoring, user survey

---

### 3.2 Scoring Accuracy Monitoring

**Objective:** Verify scoring remains accurate over time

**Method:**
- **Quarterly:** Randomly select 20 completed screenings
- **Manual Verification:** Independently calculate scores from raw responses
- **Comparison:** Compare manual vs. system scores
- **Acceptance:** 100% agreement required

**Action if Discrepancy:**
- Immediate investigation
- Freeze report generation if critical
- Root cause analysis
- Corrective action and regression testing

---

### 3.3 Adverse Event Tracking

**Definition:** Any undesirable clinical outcome potentially related to device use

**Examples:**
- Patient harmed due to false reassurance
- Delayed treatment due to system failure
- Privacy breach
- Incorrect clinical decision based on report

**Tracking:**
- All adverse events logged in dedicated database
- Severity classification (minor, moderate, severe, critical)
- Causality assessment (definite, probable, possible, unlikely, unrelated)

**Reporting:**
- **Definite/Probable + Severe/Critical:** Report to CDSCO within 24 hours
- **All Others:** Include in quarterly PMS report

---

## 4. PERFORMANCE MONITORING

### 4.1 System Availability

**Metric:** Uptime percentage  
**Target:** ≥99.5% (excluding planned maintenance)  
**Monitoring:** Automated health checks every 5 minutes

**Action if Below Target:**
- Root cause analysis
- Infrastructure review
- Implement redundancy if needed

---

### 4.2 Response Time

**Metric:** Average API response time  
**Target:** <500ms for 95th percentile  
**Monitoring:** Application performance monitoring (APM)

**Action if Above Target:**
- Performance profiling
- Database query optimization
- Scaling infrastructure

---

### 4.3 Data Integrity

**Metric:** Database constraint violations  
**Target:** 0 violations  
**Monitoring:** Weekly database integrity checks

**Action if Violations Found:**
- Immediate investigation
- Data correction if needed
- Code fix to prevent recurrence

---

## 5. CLINICAL PERFORMANCE MONITORING

### 5.1 Score Distribution Analysis

**Objective:** Verify score distributions match expected patterns from literature

**Method:**
- **Quarterly:** Analyze distribution of PHQ-9 and GAD-7 scores
- **Comparison:** Compare to published population distributions
- **Expected (PHQ-9):**
  - Minimal (0-4): ~40-50%
  - Mild (5-9): ~20-30%
  - Moderate (10-14): ~15-20%
  - Moderately Severe (15-19): ~5-10%
  - Severe (20-27): ~5-10%

**Action if Deviation:**
- Investigate potential causes (population difference, scoring bug)
- User survey to understand patient population
- Clinical review of sample reports

---

### 5.2 Clinician Review Patterns

**Objective:** Ensure clinicians are reviewing reports appropriately

**Metrics:**
- % of reports reviewed within 24 hours
- % of CRITICAL flags reviewed within 24 hours
- Average time from PROVISIONAL to REVIEWED

**Targets:**
- All reports: 90% reviewed within 48 hours
- CRITICAL flags: 100% reviewed within 24 hours

**Action if Below Target:**
- User feedback: Are notifications working?
- Workflow review: Is review process too burdensome?
- Training: Do clinicians understand importance?

---

## 6. LITERATURE SURVEILLANCE

### 6.1 Instrument Updates

**Objective:** Monitor for updates to psychometric instruments (e.g., PHQ-9 revisions)

**Method:**
- **Annual:** Literature search for new validation studies
- **Keywords:** "PHQ-9 update", "GAD-7 revision", "psychometric validation"
- **Databases:** PubMed, PsycINFO

**Action if Update Found:**
- Clinical review: Is update applicable?
- Regulatory assessment: Does update require device change?
- Implementation: Update scoring if needed, re-validate

---

### 6.2 New Evidence

**Objective:** Monitor for new clinical evidence affecting device use

**Examples:**
- New severity band recommendations
- Updated red flag thresholds
- Digital administration validation studies

**Action if Relevant Evidence Found:**
- Clinical evaluation update
- Regulatory submission if device change needed
- User notification if practice change recommended

---

## 7. COMPLAINT HANDLING

### 7.1 Complaint Categories

**Technical Complaints:**
- System unavailable
- PDF generation failure
- Incorrect score (alleged)
- Usability issue

**Clinical Complaints:**
- Inaccurate screening
- Missed red flag
- Misleading report

**Security/Privacy Complaints:**
- Unauthorized access
- Data breach
- Privacy concern

---

### 7.2 Complaint Investigation Process

1. **Receipt:** Log complaint with unique ID
2. **Acknowledgment:** Respond to complainant within 24 hours
3. **Classification:** Categorize by type and severity
4. **Investigation:** Root cause analysis
5. **Resolution:** Corrective action if needed
6. **Follow-up:** Notify complainant of outcome
7. **Trending:** Quarterly review for patterns

---

## 8. PMS REPORTING

### 8.1 Quarterly PMS Report

**Contents:**
- Summary of metrics (see Section 2.1)
- User feedback summary
- Incident log
- Adverse events
- Complaints summary
- Trending analysis
- Corrective actions taken
- Recommendations

**Distribution:**
- Internal: Management, regulatory affairs, engineering
- External: Regulatory authority (if required)

---

### 8.2 Annual PMS Summary

**Contents:**
- Aggregate data from all quarters
- Year-over-year trends
- Clinical performance summary
- Safety summary
- Literature surveillance findings
- Planned improvements for next year

**Distribution:**
- Internal: Executive leadership
- External: Regulatory authority (annual report)

---

## 9. CORRECTIVE AND PREVENTIVE ACTIONS (CAPA)

### 9.1 CAPA Triggers
- Adverse event (definite/probable causality)
- Recurring complaint (≥3 similar complaints)
- Metric exceeds threshold
- Incident investigation finding

### 9.2 CAPA Process
1. **Identify:** Problem identified via PMS
2. **Investigate:** Root cause analysis
3. **Correct:** Immediate fix for specific issue
4. **Prevent:** Systemic fix to prevent recurrence
5. **Verify:** Confirm effectiveness
6. **Document:** CAPA record with evidence

---

## 10. PMS PLAN REVIEW AND UPDATE

### 10.1 Review Frequency
- **Quarterly:** Metrics review, adjust thresholds if needed
- **Annually:** Full PMS plan review and update
- **Ad-hoc:** Upon significant device change or incident

### 10.2 Update Triggers
- New risk identified
- Regulatory requirement change
- Metric threshold adjustment needed
- New monitoring method available

---

## 11. RESPONSIBILITIES

| Role | Responsibility |
|------|----------------|
| **Regulatory Affairs** | PMS plan ownership, regulatory reporting |
| **QA** | Complaint handling, CAPA management |
| **Engineering** | Metric collection, incident investigation |
| **Clinical Affairs** | Clinical performance review, literature surveillance |
| **Management** | Resource allocation, CAPA approval |

---

## 12. PMS DATA SOURCES

### 12.1 Internal Data
- `ClinicalAuditEvent` table (audit logs)
- Application logs (errors, performance)
- Database (score distributions, usage patterns)
- User feedback surveys
- Incident reports

### 12.2 External Data
- Regulatory authority adverse event databases
- Literature (PubMed, PsycINFO)
- User complaints (email, web form)
- Industry forums and conferences

---

## DOCUMENT CONTROL

**Prepared By:** Regulatory Affairs / QA  
**Reviewed By:** [To be completed]  
**Approved By:** [To be completed]  
**Effective Date:** 2026-02-14  
**Next Review:** 2027-02-14

---

**END OF DOCUMENT**
