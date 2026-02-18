# INSTRUCTIONS FOR USE (IFU) – NEUROVA CLINICAL ENGINE V1
**Document Version:** 1.0  
**Effective Date:** 2026-02-14  
**Device:** Neurova Clinical Engine V1

---

## 1. DEVICE IDENTIFICATION

**Device Name:** Neurova Clinical Engine V1  
**Device Type:** Software as a Medical Device (SaMD)  
**Manufacturer:** [Company Name]  
**Version:** 1.0

---

## 2. INTENDED USE

The **Neurova Clinical Engine V1** is a Software as a Medical Device (SaMD) designed to provide **structured digital screening** using **validated psychometric instruments** for mental health assessment purposes. The system facilitates the administration, scoring, and reporting of standardized mental health screening tools within licensed healthcare facilities.

> [!IMPORTANT]
> **This device does NOT diagnose, treat, prescribe, or autonomously interpret mental health conditions.**

---

## 3. INTENDED USERS

**Licensed healthcare facilities with mental health professionals**, including but not limited to:
- Psychiatrists
- Clinical Psychologists
- Licensed Clinical Social Workers
- Psychiatric Nurse Practitioners
- Mental Health Counselors
- Other licensed mental health professionals operating within their scope of practice

---

## 4. INDICATIONS FOR USE

The Neurova Clinical Engine V1 is indicated for:
- Administration of validated psychometric screening instruments
- Automated scoring of standardized mental health assessments
- Generation of structured screening summaries for clinical review
- Supporting clinical workflow in mental health screening processes

---

## 5. CONTRAINDICATIONS

> [!CAUTION]
> **Do NOT use this device for:**
> - Emergency psychiatric situations requiring immediate intervention
> - As the sole basis for diagnosis or treatment decisions
> - Crisis intervention or suicide prevention as primary tool
> - Use by individuals without appropriate clinical licensure
> - Direct-to-consumer mental health diagnosis

---

## 6. WARNINGS AND PRECAUTIONS

### 6.1 Critical Warnings

> [!WARNING]
> **Screening Only – Not a Diagnosis**
> 
> This device provides screening summaries only. All results must be reviewed and interpreted by a licensed mental health professional within the context of comprehensive clinical assessment. This screening summary is intended to support, not replace, clinical judgment.

> [!WARNING]
> **Red Flag Escalation Required**
> 
> Any screening that identifies critical responses (e.g., suicidal ideation in PHQ-9 Question 9) will be flagged as CRITICAL. These flags require immediate clinical attention and review. Do not delay review of flagged reports.

> [!WARNING]
> **Not for Crisis Use**
> 
> This device is NOT intended for use in emergency mental health crisis situations. Patients in acute crisis require immediate professional intervention, not screening tools.

### 6.2 Precautions

- **Professional Interpretation Required:** All screening results require professional clinical interpretation
- **Patient Population:** Validated for adults (18 years and older) only
- **Honest Responses:** Results depend on accuracy of patient-provided information
- **Clinical Correlation:** Screening results must be correlated with patient history and clinical presentation

---

## 7. DEVICE DESCRIPTION

### 7.1 System Components
- **Patient Interface:** Web-based screening questionnaire
- **Clinician Interface:** Report review and download portal
- **Scoring Engine:** Automated calculation based on validated algorithms
- **Report Generator:** PDF report creation with disclaimers
- **Audit System:** Comprehensive event logging

### 7.2 Screening Instruments Included
- **PHQ-9:** Patient Health Questionnaire (Depression Screening)
- **GAD-7:** Generalized Anxiety Disorder Scale
- Additional validated instruments as configured

---

## 8. OPERATING INSTRUCTIONS

### 8.1 Creating a Screening Order

1. **Log in** to the Neurova Clinical Engine clinician portal
2. **Create New Order:**
   - Enter patient demographic information
   - Select screening battery (e.g., PHQ-9, GAD-7)
   - Generate unique screening link
3. **Share Link:** Provide screening link to patient via secure method
4. **Patient Consent:** Patient must review and accept consent before screening begins

### 8.2 Patient Screening Process

1. **Access Link:** Patient clicks on provided screening link
2. **Review Consent:** Patient reads and accepts informed consent
3. **Complete Screening:** Patient answers all questions honestly
   - Questions presented one at a time
   - Progress saved automatically
   - Can pause and resume within 24 hours
4. **Submission:** Patient submits completed screening

### 8.3 Clinician Review Process

1. **Notification:** Clinician notified when screening is complete
2. **Review Report:**
   - Access clinician portal
   - View screening summary
   - **CRITICAL:** Check for red flags (highlighted in red)
3. **Clinical Interpretation:**
   - Correlate screening results with clinical assessment
   - Consider patient history and presentation
   - **Do not rely solely on screening scores for clinical decisions**
4. **Mark as Reviewed:** Update report status to REVIEWED after clinical review

### 8.4 Downloading PDF Report

1. **Request Download:** Click "Download PDF" in clinician portal
2. **OTP Verification:** Enter one-time password sent to registered email
3. **Download:** PDF report downloads to device
4. **Security:** Do not share OTP or PDF via unsecured channels

---

## 9. INTERPRETING SCREENING RESULTS

### 9.1 Understanding Severity Bands

**PHQ-9 (Depression Screening):**
| Score Range | Severity Band | Clinical Consideration |
|-------------|---------------|------------------------|
| 0-4 | Minimal | Watchful waiting |
| 5-9 | Mild | Repeat screening at follow-up |
| 10-14 | Moderate | Consider treatment plan |
| 15-19 | Moderately Severe | Active treatment recommended |
| 20-27 | Severe | Immediate treatment, consider hospitalization |

**GAD-7 (Anxiety Screening):**
| Score Range | Severity Band | Clinical Consideration |
|-------------|---------------|------------------------|
| 0-4 | Minimal | Watchful waiting |
| 5-9 | Mild | Repeat screening at follow-up |
| 10-14 | Moderate | Consider treatment plan |
| 15-21 | Severe | Active treatment recommended |

> [!IMPORTANT]
> **These are screening severity bands, NOT diagnostic categories.** Clinical judgment and comprehensive assessment are required for diagnosis and treatment planning.

### 9.2 Red Flag Responses

**PHQ-9 Question 9 (Suicidal Ideation):**
- **Question:** "Thoughts that you would be better off dead or of hurting yourself"
- **Red Flag Threshold:** Any response other than "Not at all"
- **Action Required:** Immediate clinical attention and risk assessment

**Report Status:**
- **DRAFT:** Screening in progress, not yet submitted
- **PROVISIONAL:** Screening complete, awaiting clinical review (or contains CRITICAL flag)
- **REVIEWED:** Clinician has reviewed and marked as reviewed

> [!CAUTION]
> **All reports with CRITICAL flags default to PROVISIONAL status and display watermark: "PROVISIONAL – NOT CLINICALLY REVIEWED" until clinician review is completed.**

---

## 10. LIMITATIONS

### 10.1 Device Limitations
- **Screening Only:** Not a diagnostic tool
- **Requires Professional Oversight:** Cannot be used autonomously
- **Age Limitation:** Not validated for pediatric populations (<18 years)
- **Self-Report Dependency:** Accuracy depends on patient honesty
- **Sensitivity/Specificity:** Not 100% (false positives and negatives possible)

### 10.2 Technical Limitations
- **Internet Required:** Requires stable internet connection
- **Device Compatibility:** Requires modern web browser (Chrome, Firefox, Safari, Edge)
- **Literacy Required:** Patient must be able to read and understand questions
- **Technical Literacy:** Basic familiarity with digital devices required

---

## 11. TROUBLESHOOTING

| Problem | Possible Cause | Solution |
|---------|----------------|----------|
| Patient cannot access screening link | Link expired (>24 hours) | Generate new screening link |
| Screening progress lost | Network interruption | Patient can resume from last saved question |
| PDF download fails | OTP expired or incorrect | Request new OTP |
| Report shows "PROVISIONAL" watermark | Contains CRITICAL flag or not yet reviewed | Complete clinical review, mark as REVIEWED |
| Cannot log in | Incorrect credentials | Reset password or contact support |

---

## 12. MAINTENANCE AND SUPPORT

### 12.1 Software Updates
- **Automatic Updates:** System updates applied during scheduled maintenance windows
- **User Notification:** Users notified of updates via email
- **No User Action Required:** Updates do not require user intervention

### 12.2 Technical Support
- **Email:** [support email]
- **Phone:** [support phone]
- **Hours:** [support hours]
- **Response Time:** Within 24 hours for non-critical issues, within 2 hours for critical issues

---

## 13. ADVERSE EVENT REPORTING

### 13.1 What to Report
Report any incident where the device:
- Contributed to patient harm
- Malfunctioned or produced incorrect results
- Was involved in a near-miss safety event

### 13.2 How to Report
- **Email:** [adverse event email]
- **Include:**
  - Date and time of incident
  - Device version
  - Description of event
  - Patient impact (if any)
  - Your contact information

---

## 14. STORAGE AND ENVIRONMENTAL CONDITIONS

### 14.1 Operating Environment
- **Temperature:** 10°C to 35°C (50°F to 95°F)
- **Humidity:** 20% to 80% non-condensing
- **Network:** Stable internet connection required

### 14.2 Data Storage
- **Location:** Secure cloud infrastructure
- **Encryption:** Data encrypted at rest and in transit
- **Backup:** Daily automated backups
- **Retention:** Per data governance policy (see Section 15)

---

## 15. DATA PRIVACY AND RETENTION

### 15.1 Data Protection
- **Encryption:** All patient data encrypted (AES-256)
- **Access Control:** Role-based access, OTP-protected reports
- **Audit Logging:** All access logged and monitored

### 15.2 Data Retention
- **Active Records:** Retained per facility policy
- **Deletion Requests:** Processed within 30 days
- **Audit Logs:** Retained for 7 years (regulatory requirement)

---

## 16. REGULATORY INFORMATION

**Regulatory Status:** [To be completed upon approval]  
**Classification:** Software as a Medical Device (SaMD)  
**Standards Compliance:**
- ISO 14971 (Risk Management)
- IEC 62304 (Software Lifecycle)
- IEC 62366-1 (Usability Engineering)

---

## 17. SYMBOLS AND LABELS

| Symbol | Meaning |
|--------|---------|
| **SCREENING SUMMARY** | Output is screening tool, not diagnosis |
| **PROVISIONAL** | Requires clinical review |
| **CRITICAL** | Red flag identified, immediate attention required |
| **REVIEWED** | Clinician has completed review |

---

## 18. WARRANTY AND LIABILITY

**Warranty:** [To be completed by manufacturer]  
**Liability Disclaimer:** This device is a screening tool only. Clinical decisions remain the sole responsibility of licensed healthcare professionals. The manufacturer is not liable for clinical decisions made based on screening results.

---

## 19. CONTACT INFORMATION

**Manufacturer:** [Company Name]  
**Address:** [Company Address]  
**Email:** [Company Email]  
**Phone:** [Company Phone]  
**Website:** [Company Website]

---

## 20. DOCUMENT REVISION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-14 | Initial release |

---

## APPENDIX A: STANDARD DISCLAIMER TEXT

**The following disclaimer appears on all PDF reports and UI screens:**

> **SCREENING SUMMARY – NOT A DIAGNOSIS**
> 
> This document contains screening results generated by the Neurova Clinical Engine V1, a Software as a Medical Device (SaMD) designed for structured digital screening using validated psychometric instruments.
> 
> **This system does NOT diagnose, treat, prescribe, or autonomously interpret mental health conditions.**
> 
> All screening results must be reviewed and interpreted by a licensed mental health professional within the context of comprehensive clinical assessment. This screening summary is intended to support, not replace, clinical judgment.
> 
> **For use only by licensed healthcare facilities with qualified mental health professionals.**

---

**END OF DOCUMENT**

**For questions or support, contact:** [support contact]
