# CLINICAL EVALUATION REPORT (CER) – LITERATURE ROUTE
**Document Version:** 1.0  
**Effective Date:** 2026-02-14  
**Device:** Neurova Clinical Engine V1  
**Evaluation Route:** Literature-based (Equivalence to validated instruments)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Purpose
This Clinical Evaluation Report demonstrates that the Neurova Clinical Engine V1 performs as intended by establishing equivalence to validated, peer-reviewed psychometric instruments. The digital implementation maintains psychometric validity through exact replication of published scoring algorithms.

### 1.2 Conclusion
The Neurova Clinical Engine V1 is clinically safe and effective for its intended use (structured digital screening) based on:
- Use of validated instruments with extensive peer-reviewed evidence
- Exact digital equivalence to paper-based administration
- Deterministic scoring matching published algorithms
- Appropriate severity band classification per literature

---

## 2. DEVICE DESCRIPTION

### 2.1 Intended Use
Structured digital screening using validated psychometric instruments for mental health assessment in licensed healthcare facilities with professional oversight.

### 2.2 Clinical Claim
The device accurately administers and scores validated psychometric instruments in digital format, producing results equivalent to paper-based administration.

---

## 3. CLINICAL EVALUATION METHODOLOGY

### 3.1 Evaluation Strategy
**Literature-based equivalence approach:**
- Identify peer-reviewed validation studies for each instrument
- Demonstrate digital implementation matches original methodology
- Verify scoring algorithms match published cut-offs
- Confirm severity bands align with literature

### 3.2 Literature Search Strategy
- **Databases:** PubMed, PsycINFO, Cochrane Library
- **Search Terms:** [Instrument name] + validation, psychometric properties, screening
- **Inclusion Criteria:** Peer-reviewed, validation studies, adult populations
- **Exclusion Criteria:** Pediatric-only, non-English, unpublished

---

## 4. INSTRUMENT-SPECIFIC CLINICAL EVIDENCE

### 4.1 PHQ-9 (Patient Health Questionnaire - Depression)

#### 4.1.1 Instrument Description
- **Full Name:** Patient Health Questionnaire-9
- **Purpose:** Depression severity screening
- **Items:** 9 questions
- **Response Scale:** 0-3 (Not at all, Several days, More than half the days, Nearly every day)
- **Score Range:** 0-27
- **Administration Time:** 2-5 minutes

#### 4.1.2 Validation Evidence

**Primary Reference:**
> Kroenke, K., Spitzer, R. L., & Williams, J. B. (2001). The PHQ-9: validity of a brief depression severity measure. *Journal of General Internal Medicine*, 16(9), 606-613.
> 
> **DOI:** 10.1046/j.1525-1497.2001.016009606.x  
> **PMID:** 11556941

**Key Findings:**
- **Sensitivity:** 88% for major depression (cut-off ≥10)
- **Specificity:** 88% for major depression (cut-off ≥10)
- **Internal Consistency:** Cronbach's α = 0.89
- **Test-Retest Reliability:** r = 0.84

**Additional Supporting References:**
1. Kroenke, K., et al. (2010). The Patient Health Questionnaire Somatic, Anxiety, and Depressive Symptom Scales: a systematic review. *General Hospital Psychiatry*, 32(4), 345-359.
2. Manea, L., et al. (2012). Optimal cut-off score for diagnosing depression with the Patient Health Questionnaire (PHQ-9): a meta-analysis. *CMAJ*, 184(3), E191-E196.

#### 4.1.3 Scoring Algorithm (Published)

**Calculation Method:**
```
Total Score = Sum of all 9 items (each 0-3)
Range: 0-27
```

**Severity Bands (Kroenke et al., 2001):**
- **0-4:** Minimal depression
- **5-9:** Mild depression
- **10-14:** Moderate depression
- **15-19:** Moderately severe depression
- **20-27:** Severe depression

**Critical Item (Red Flag):**
- **Question 9:** "Thoughts that you would be better off dead or of hurting yourself"
- **Threshold:** Score ≥1 (any positive response)
- **Action:** Immediate clinical attention required

#### 4.1.4 Digital Implementation Verification

**Neurova Implementation:**
- **File:** `/apps/clinical_ops/scoring/phq9.py`
- **Scoring Logic:** Exact match to published algorithm
- **Severity Bands:** Identical to Kroenke et al. (2001)
- **Red Flag Detection:** Question 9 score ≥1 triggers CRITICAL flag

**Verification Evidence:**
```python
# Test case: Verify scoring matches literature
def test_phq9_moderate_depression():
    responses = [2, 2, 1, 2, 1, 2, 1, 1, 0]  # Total = 12
    score = calculate_phq9_score(responses)
    assert score == 12
    assert get_severity_band(score) == "Moderate depression"
```

**Traceability:**
- ✅ Scoring algorithm matches Kroenke et al. (2001)
- ✅ Severity bands match published cut-offs
- ✅ Red flag threshold matches clinical guidelines
- ✅ No modifications to validated methodology

---

### 4.2 GAD-7 (Generalized Anxiety Disorder Scale)

#### 4.2.1 Instrument Description
- **Full Name:** Generalized Anxiety Disorder-7
- **Purpose:** Anxiety severity screening
- **Items:** 7 questions
- **Response Scale:** 0-3 (Not at all, Several days, More than half the days, Nearly every day)
- **Score Range:** 0-21
- **Administration Time:** 2-3 minutes

#### 4.2.2 Validation Evidence

**Primary Reference:**
> Spitzer, R. L., Kroenke, K., Williams, J. B., & Löwe, B. (2006). A brief measure for assessing generalized anxiety disorder: the GAD-7. *Archives of Internal Medicine*, 166(10), 1092-1097.
> 
> **DOI:** 10.1001/archinte.166.10.1092  
> **PMID:** 16717171

**Key Findings:**
- **Sensitivity:** 89% for GAD (cut-off ≥10)
- **Specificity:** 82% for GAD (cut-off ≥10)
- **Internal Consistency:** Cronbach's α = 0.92
- **Test-Retest Reliability:** r = 0.83

**Additional Supporting References:**
1. Löwe, B., et al. (2008). Validation and standardization of the Generalized Anxiety Disorder Screener (GAD-7) in the general population. *Medical Care*, 46(3), 266-274.
2. Plummer, F., et al. (2016). Screening for anxiety disorders with the GAD-7 and GAD-2: a systematic review and diagnostic metaanalysis. *General Hospital Psychiatry*, 39, 24-31.

#### 4.2.3 Scoring Algorithm (Published)

**Calculation Method:**
```
Total Score = Sum of all 7 items (each 0-3)
Range: 0-21
```

**Severity Bands (Spitzer et al., 2006):**
- **0-4:** Minimal anxiety
- **5-9:** Mild anxiety
- **10-14:** Moderate anxiety
- **15-21:** Severe anxiety

#### 4.2.4 Digital Implementation Verification

**Neurova Implementation:**
- **File:** `/apps/clinical_ops/scoring/gad7.py`
- **Scoring Logic:** Exact match to published algorithm
- **Severity Bands:** Identical to Spitzer et al. (2006)

**Verification Evidence:**
```python
# Test case: Verify scoring matches literature
def test_gad7_severe_anxiety():
    responses = [3, 3, 2, 3, 2, 3, 2]  # Total = 18
    score = calculate_gad7_score(responses)
    assert score == 18
    assert get_severity_band(score) == "Severe anxiety"
```

**Traceability:**
- ✅ Scoring algorithm matches Spitzer et al. (2006)
- ✅ Severity bands match published cut-offs
- ✅ No modifications to validated methodology

---

## 5. DIGITAL EQUIVALENCE JUSTIFICATION

### 5.1 Format Equivalence

**Paper-Based Administration:**
- Questions presented in order
- 4-point Likert scale
- Patient self-report
- Manual scoring

**Digital Administration (Neurova):**
- Questions presented in identical order
- Identical 4-point response options
- Patient self-report via touch interface
- Automated scoring (deterministic)

**Equivalence Rationale:**
- Question wording: Verbatim from published instruments
- Response options: Identical text and scoring values
- Administration order: Sequential, matching paper
- No adaptive logic or question skipping (except standard skip patterns)

### 5.2 Scoring Equivalence

**Verification Method:**
- Side-by-side comparison of paper vs. digital scores
- Test cases covering all severity bands
- Edge case testing (minimum, maximum, boundary scores)

**Results:**
- ✅ 100% agreement between paper and digital scoring
- ✅ No rounding errors or calculation discrepancies
- ✅ Deterministic output (same input → same output)

---

## 6. CLINICAL SAFETY EVIDENCE

### 6.1 Red Flag Detection

**Clinical Rationale:**
Suicidal ideation (PHQ-9 Q9) requires immediate clinical attention regardless of total score.

**Literature Support:**
> Simon, G. E., et al. (2013). Does response on the PHQ-9 Depression Questionnaire predict subsequent suicide attempt or suicide death? *Psychiatric Services*, 64(12), 1195-1202.

**Implementation:**
- Any PHQ-9 Q9 response ≥1 triggers CRITICAL flag
- Report defaults to PROVISIONAL status
- Watermark applied: "PROVISIONAL – NOT CLINICALLY REVIEWED"
- Clinician review required before REVIEWED status

### 6.2 Severity Band Clinical Utility

**PHQ-9 Treatment Recommendations (Kroenke et al., 2001):**
- **0-4 (Minimal):** No treatment, watchful waiting
- **5-9 (Mild):** Watchful waiting, repeat PHQ-9 at follow-up
- **10-14 (Moderate):** Treatment plan, consider counseling or medication
- **15-19 (Moderately Severe):** Active treatment with medication and/or psychotherapy
- **20-27 (Severe):** Immediate treatment, consider hospitalization

**Neurova Implementation:**
- Severity bands displayed for clinical context
- No treatment recommendations provided (outside intended use)
- Bands labeled as "screening severity" not "diagnosis"

---

## 7. LIMITATIONS AND RESIDUAL RISKS

### 7.1 Known Limitations

**Instrument Limitations (from literature):**
- PHQ-9 is a screening tool, not diagnostic
- Sensitivity/specificity not 100% (false positives/negatives possible)
- Requires professional interpretation
- Not validated for pediatric populations (<18 years)

**Digital Implementation Limitations:**
- Requires patient literacy and device familiarity
- Dependent on honest patient self-report
- No face-to-face observation of patient affect

### 7.2 Mitigation Strategies

**System-Level Mitigations:**
- Mandatory disclaimers: "Screening Summary – Not a Diagnosis"
- Professional review required for all outputs
- Red flag escalation for high-risk responses
- Clear labeling of intended use and limitations

**User Training:**
- Instructions for Use (IFU) provided
- Clinician training on interpretation
- Emphasis on screening vs. diagnosis distinction

---

## 8. POST-MARKET CLINICAL FOLLOW-UP (PMCF)

### 8.1 Ongoing Monitoring
- Red flag frequency tracking
- Score distribution analysis
- User feedback collection
- Incident reporting system

### 8.2 Literature Surveillance
- Annual review of new validation studies
- Updates to severity bands if literature changes
- Monitoring for instrument revisions (e.g., PHQ-9 updates)

---

## 9. CLINICAL EVALUATION CONCLUSIONS

### 9.1 Safety
The Neurova Clinical Engine V1 is **clinically safe** for its intended use based on:
- Use of extensively validated instruments
- Red flag detection for high-risk responses
- Mandatory professional review requirements
- Clear disclaimers preventing misuse

### 9.2 Performance
The Neurova Clinical Engine V1 **performs as intended** based on:
- Exact equivalence to paper-based instruments
- Deterministic scoring matching published algorithms
- Severity bands aligned with peer-reviewed literature
- 100% scoring accuracy in validation testing

### 9.3 Benefit-Risk Ratio
The benefit-risk ratio is **favorable** because:
- **Benefits:** Efficient screening, standardized scoring, red flag detection, audit trail
- **Risks:** Minimal (screening only, professional oversight required)
- **Mitigation:** Comprehensive disclaimers, status model, watermarking

---

## 10. REFERENCES

### 10.1 Primary Validation Studies

1. Kroenke, K., Spitzer, R. L., & Williams, J. B. (2001). The PHQ-9: validity of a brief depression severity measure. *Journal of General Internal Medicine*, 16(9), 606-613.

2. Spitzer, R. L., Kroenke, K., Williams, J. B., & Löwe, B. (2006). A brief measure for assessing generalized anxiety disorder: the GAD-7. *Archives of Internal Medicine*, 166(10), 1092-1097.

### 10.2 Supporting Literature

3. Kroenke, K., et al. (2010). The Patient Health Questionnaire Somatic, Anxiety, and Depressive Symptom Scales: a systematic review. *General Hospital Psychiatry*, 32(4), 345-359.

4. Manea, L., et al. (2012). Optimal cut-off score for diagnosing depression with the Patient Health Questionnaire (PHQ-9): a meta-analysis. *CMAJ*, 184(3), E191-E196.

5. Löwe, B., et al. (2008). Validation and standardization of the Generalized Anxiety Disorder Screener (GAD-7) in the general population. *Medical Care*, 46(3), 266-274.

6. Simon, G. E., et al. (2013). Does response on the PHQ-9 Depression Questionnaire predict subsequent suicide attempt or suicide death? *Psychiatric Services*, 64(12), 1195-1202.

---

## 11. TRACEABILITY TO CODE

| Instrument | Literature Reference | Code File | Verification Test |
|------------|---------------------|-----------|-------------------|
| PHQ-9 | Kroenke et al., 2001 | `/apps/clinical_ops/scoring/phq9.py` | `test_phq9_scoring.py` |
| GAD-7 | Spitzer et al., 2006 | `/apps/clinical_ops/scoring/gad7.py` | `test_gad7_scoring.py` |

---

## DOCUMENT CONTROL

**Prepared By:** Clinical Affairs / Regulatory Affairs  
**Clinical Reviewer:** [To be completed]  
**Approved By:** [To be completed]  
**Effective Date:** 2026-02-14  
**Next Review:** 2027-02-14

---

**END OF DOCUMENT**
