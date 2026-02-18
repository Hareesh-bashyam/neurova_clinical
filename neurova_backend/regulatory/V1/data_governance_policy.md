# DATA GOVERNANCE POLICY
**Document Version:** 1.0  
**Effective Date:** 2026-02-14  
**Device:** Neurova Clinical Engine V1  
**Compliance:** DPDP Act (India), Medical Device Rules

---

## 1. OVERVIEW

### 1.1 Purpose
Establish policies for data collection, storage, retention, deletion, and export to ensure:
- Patient privacy protection
- Regulatory compliance
- Medico-legal defensibility
- Data integrity and security

### 1.2 Scope
All data collected, processed, and stored by the Neurova Clinical Engine V1, including:
- Patient demographic data
- Screening responses
- Audit logs
- User accounts
- Report metadata

---

## 2. DATA CLASSIFICATION

### 2.1 Sensitive Personal Data
**Definition:** Data requiring highest protection level

**Includes:**
- Mental health screening responses
- PHQ-9 and GAD-7 answers
- Red flag indicators
- Screening scores and severity bands

**Protection Measures:**
- Encryption at rest (AES-256)
- Encryption in transit (TLS 1.2+)
- Access control (role-based)
- OTP-protected report downloads
- Audit logging of all access

---

### 2.2 Personal Identifiable Information (PII)
**Definition:** Data that can identify an individual

**Includes:**
- Patient name
- Date of birth
- Email address (if collected)
- Phone number (if collected)
- Order ID (pseudonymized identifier)

**Protection Measures:**
- Encryption at rest and in transit
- Access restricted to authorized users
- Audit logging
- Pseudonymization where possible

---

### 2.3 Operational Data
**Definition:** Data for system operation and audit

**Includes:**
- Audit logs (user actions, access events)
- System logs (errors, performance)
- User accounts (clinician credentials)
- Session data

**Protection Measures:**
- Encryption at rest
- Access restricted to administrators
- Retention per regulatory requirements

---

## 3. DATA RETENTION POLICY

### 3.1 Active Data Retention

| Data Type | Retention Period | Rationale |
|-----------|------------------|-----------|
| Screening responses | Per facility policy (minimum 7 years) | Medical record requirement |
| Audit logs | 7 years | Regulatory requirement |
| System logs | 90 days | Operational troubleshooting |
| User accounts | Duration of employment + 1 year | Access control audit |
| Session data | 24 hours | Temporary operational data |

### 3.2 Deletion Triggers
- **Patient Request:** Data deletion upon verified patient request
- **Facility Request:** Data deletion upon facility request (with patient consent)
- **Retention Expiry:** Automatic deletion after retention period
- **Account Closure:** User account deletion 1 year after deactivation

---

## 4. DATA DELETION WORKFLOW

### 4.1 Deletion Request Process

**Step 1: Request Submission**
- Patient or facility submits deletion request via secure form
- Request includes: Patient identifier, reason for deletion, requestor identity

**Step 2: Identity Verification**
- Verify requestor identity (OTP, facility credentials)
- Confirm requestor authority (patient or authorized facility representative)

**Step 3: Regulatory Review**
- Check if data subject to legal hold or regulatory requirement
- Confirm retention period has expired (if applicable)
- Approve or deny request

**Step 4: Deletion Execution**
- Mark records for deletion in `DeletionRequest` model
- Execute deletion within 30 days of approval
- Delete from:
  - Primary database
  - Backups (next backup cycle)
  - Logs (anonymize identifiers)

**Step 5: Confirmation**
- Audit log deletion event
- Notify requestor of completion
- Generate deletion certificate (if requested)

### 4.2 DeletionRequest Model

**Database Fields:**
```python
class DeletionRequest(models.Model):
    request_id = UUIDField(primary_key=True)
    order_id = ForeignKey(Order)
    requestor_type = CharField(choices=['PATIENT', 'FACILITY'])
    requestor_identity = CharField()  # Email or facility ID
    reason = TextField()
    request_date = DateTimeField(auto_now_add=True)
    approval_status = CharField(choices=['PENDING', 'APPROVED', 'DENIED'])
    approval_date = DateTimeField(null=True)
    deletion_date = DateTimeField(null=True)
    deleted_by = ForeignKey(User, null=True)
```

### 4.3 Audit Log of Deletion

**Required Fields:**
- Deletion request ID
- Order ID (before deletion)
- Requestor identity
- Approval authority
- Deletion timestamp
- Data types deleted

**Retention:** Deletion audit logs retained for 7 years (even after data deletion)

---

## 5. DATA EXPORT CAPABILITY

### 5.1 Patient Data Export

**Purpose:** Enable patients to exercise data portability rights

**Export Format:** JSON (machine-readable) or PDF (human-readable)

**Export Contents:**
- All screening responses
- Screening scores and severity bands
- Timestamps (screening start, completion, review)
- Report status history
- Audit log (patient-specific events)

**Access Method:**
- Patient requests export via facility
- Facility verifies patient identity
- Facility generates export and provides to patient

### 5.2 Facility Data Export

**Purpose:** Enable facility to export data for migration or backup

**Export Format:** JSON (structured data) or CSV (tabular data)

**Export Contents:**
- All orders and responses
- Audit logs
- User accounts (excluding passwords)
- Report metadata

**Access Method:**
- Facility administrator requests export
- Export generated with encryption
- Secure download link (OTP-protected)

---

## 6. ENCRYPTION REQUIREMENTS

### 6.1 Encryption at Rest

**Database Encryption:**
- **Method:** PostgreSQL Transparent Data Encryption (TDE) or disk-level encryption
- **Algorithm:** AES-256
- **Key Management:** Separate key management service (KMS)
- **Key Rotation:** Annual key rotation

**Backup Encryption:**
- All backups encrypted with AES-256
- Separate encryption keys from production
- Secure key storage

### 6.2 Encryption in Transit

**HTTPS Enforcement:**
- **Protocol:** TLS 1.2 or higher
- **Certificate:** Valid SSL/TLS certificate from trusted CA
- **HTTP Redirect:** All HTTP requests redirected to HTTPS
- **HSTS:** HTTP Strict Transport Security header enabled

**API Communication:**
- All API requests over HTTPS
- No sensitive data in URL parameters
- Authentication tokens in headers only

---

## 7. ACCESS CONTROL

### 7.1 Role-Based Access Control (RBAC)

| Role | Access Level | Permissions |
|------|--------------|-------------|
| **Patient** | Own data only | View own screening, submit responses |
| **Clinician** | Facility patients | Create orders, review reports, download PDFs |
| **Facility Admin** | All facility data | User management, data export, deletion requests |
| **System Admin** | All data (read-only) | System monitoring, troubleshooting (no PHI modification) |

### 7.2 OTP-Protected Access

**Report Downloads:**
- OTP sent to clinician's registered email
- OTP valid for 10 minutes
- Maximum 3 OTP attempts
- Rate limiting: 5 OTP requests per hour per user

**Data Exports:**
- OTP required for all data exports
- Export link expires after 24 hours
- Single-use download link

---

## 8. AUDIT LOGGING

### 8.1 Logged Events

**Patient Data Access:**
- Screening started
- Screening completed
- Report viewed
- PDF downloaded
- Data exported

**Data Modifications:**
- Order created
- Status changed (DRAFT → PROVISIONAL → REVIEWED)
- Deletion request submitted
- Deletion executed

**Security Events:**
- Login attempts (success/failure)
- OTP requests
- Invalid OTP attempts
- Unauthorized access attempts

### 8.2 Audit Log Contents

**Required Fields:**
- Event type
- Timestamp (UTC)
- User ID (who performed action)
- Patient ID (whose data was accessed)
- IP address
- Action result (success/failure)
- Additional context (e.g., order ID, report ID)

### 8.3 Audit Log Retention
- **Retention Period:** 7 years
- **Access:** Restricted to authorized personnel
- **Immutability:** Audit logs cannot be modified or deleted (append-only)

---

## 9. DATA BREACH RESPONSE

### 9.1 Breach Definition
Unauthorized access, disclosure, or loss of patient data.

### 9.2 Breach Response Procedure

**Step 1: Detection and Containment (0-2 hours)**
- Identify breach scope (what data, how many patients)
- Contain breach (disable compromised accounts, block access)
- Preserve evidence (logs, system state)

**Step 2: Assessment (2-24 hours)**
- Assess severity (number of patients, data sensitivity)
- Determine root cause
- Identify affected individuals

**Step 3: Notification (24-72 hours)**
- **Regulatory Authority:** Notify within 72 hours (DPDP requirement)
- **Affected Patients:** Notify within 72 hours
- **Facility:** Notify immediately

**Step 4: Remediation**
- Implement corrective actions
- Enhance security controls
- Update policies and procedures

**Step 5: Documentation**
- Breach report with timeline
- Root cause analysis
- Corrective actions taken
- Lessons learned

---

## 10. DATA MINIMIZATION

### 10.1 Principle
Collect only data necessary for intended use.

### 10.2 Implementation
- **No Optional Fields:** Only collect required demographic data
- **No Free Text:** Avoid collecting narrative notes (unless required for instrument)
- **Pseudonymization:** Use order IDs instead of patient names where possible
- **Temporary Data:** Delete session data after 24 hours

---

## 11. THIRD-PARTY DATA SHARING

### 11.1 Policy
**No third-party data sharing** without explicit patient consent and facility authorization.

### 11.2 Exceptions
- **Legal Requirement:** Court order or regulatory mandate
- **Service Providers:** Cloud infrastructure providers (with data processing agreements)
- **Emergency:** Immediate threat to patient safety (with documentation)

### 11.3 Data Processing Agreements
All service providers must sign Data Processing Agreements (DPAs) including:
- Confidentiality obligations
- Security requirements
- Data breach notification
- Subprocessor restrictions
- Audit rights

---

## 12. PATIENT RIGHTS

### 12.1 Right to Access
Patients can request copy of their data via facility.

### 12.2 Right to Rectification
Patients can request correction of inaccurate data (with clinical review).

### 12.3 Right to Erasure
Patients can request deletion of data (subject to regulatory retention requirements).

### 12.4 Right to Data Portability
Patients can request export of data in machine-readable format.

### 12.5 Right to Object
Patients can object to data processing (results in inability to use service).

---

## 13. COMPLIANCE MONITORING

### 13.1 Internal Audits
- **Frequency:** Quarterly
- **Scope:** Access logs, encryption verification, retention compliance
- **Reporting:** Findings reported to management

### 13.2 External Audits
- **Frequency:** Annual (or as required by regulator)
- **Scope:** Full data governance compliance
- **Certification:** ISO 27001 (Information Security Management)

---

## 14. TRAINING

### 14.1 User Training
All users (clinicians, facility admins) must complete data privacy training:
- Patient data protection principles
- Access control procedures
- Breach reporting requirements
- Deletion request handling

### 14.2 Training Frequency
- **Initial:** Before system access granted
- **Refresher:** Annually
- **Ad-hoc:** Upon policy updates

---

## 15. POLICY REVIEW AND UPDATES

### 15.1 Review Frequency
- **Annual:** Full policy review
- **Ad-hoc:** Upon regulatory changes or incidents

### 15.2 Update Process
1. Identify need for update
2. Draft policy changes
3. Legal and regulatory review
4. Management approval
5. User notification
6. Training update (if needed)

---

## DOCUMENT CONTROL

**Prepared By:** Data Privacy Officer / Regulatory Affairs  
**Reviewed By:** [To be completed]  
**Approved By:** [To be completed]  
**Effective Date:** 2026-02-14  
**Next Review:** 2027-02-14

---

**END OF DOCUMENT**
