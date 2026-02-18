# SOUP ANALYSIS (Software of Unknown Provenance)
**Document Version:** 1.0  
**Effective Date:** 2026-02-14  
**Device:** Neurova Clinical Engine V1  
**Standard:** IEC 62304 (Medical Device Software Lifecycle)

---

## 1. SOUP OVERVIEW

### 1.1 Definition
**SOUP (Software of Unknown Provenance):** Software item that is already developed and generally available, for which adequate records of the development process are not available.

### 1.2 Purpose
Identify and analyze all third-party software dependencies to:
- Assess criticality to device safety
- Document known limitations
- Implement mitigations for risks
- Ensure use of stable, maintained versions

---

## 2. SOUP INVENTORY

### SOUP-001: Django

**Component Name:** Django Web Framework  
**Version:** 4.2 LTS  
**Vendor:** Django Software Foundation  
**License:** BSD 3-Clause  
**Website:** https://www.djangoproject.com/

**Purpose in Device:**
- Web application framework
- Database ORM (Object-Relational Mapping)
- Request/response handling
- User authentication
- Admin interface

**Criticality:** **HIGH**
- Core framework for entire application
- Handles all HTTP requests
- Manages database transactions
- Security-critical (authentication, CSRF protection)

**Known Limitations:**
- Security vulnerabilities possible (requires updates)
- ORM query performance dependent on usage patterns
- Default settings may not be production-ready

**Mitigations:**
1. **LTS Version:** Use Long-Term Support version (4.2) with extended security updates
2. **Security Updates:** Monitor Django security advisories, apply patches promptly
3. **Configuration Review:** Production settings hardened (DEBUG=False, ALLOWED_HOSTS configured)
4. **Testing:** Comprehensive integration tests for critical paths
5. **Transaction Safety:** Use atomic transactions for data integrity

**Verification:**
- ✅ Version pinned in `requirements.txt`
- ✅ Security settings reviewed
- ✅ Integration tests cover transaction safety

**Residual Risk:** LOW (with LTS version and monitoring)

---

### SOUP-002: PostgreSQL

**Component Name:** PostgreSQL Database  
**Version:** 14.x (LTS)  
**Vendor:** PostgreSQL Global Development Group  
**License:** PostgreSQL License (permissive)  
**Website:** https://www.postgresql.org/

**Purpose in Device:**
- Primary data storage
- Patient responses
- Audit logs
- User accounts
- Report metadata

**Criticality:** **CRITICAL**
- All patient data stored here
- Data loss = catastrophic failure
- Data corruption = incorrect scores

**Known Limitations:**
- Requires proper configuration for ACID compliance
- Backup/recovery dependent on infrastructure
- Concurrent access requires transaction isolation

**Mitigations:**
1. **LTS Version:** Use stable, long-term supported version
2. **ACID Compliance:** Ensure default transaction isolation level (READ COMMITTED)
3. **Backups:** Automated daily backups with point-in-time recovery
4. **Encryption:** Encryption at rest enabled
5. **Constraints:** Database-level constraints prevent invalid data

**Verification:**
- ✅ Version documented in infrastructure
- ✅ Backup procedures tested
- ✅ Unique constraints prevent duplicate reports

**Residual Risk:** LOW (with proper configuration and backups)

---

### SOUP-003: ReportLab

**Component Name:** ReportLab PDF Library  
**Version:** 3.6.x  
**Vendor:** ReportLab Ltd.  
**License:** BSD  
**Website:** https://www.reportlab.com/

**Purpose in Device:**
- PDF report generation
- Layout and formatting
- Watermark application
- Text rendering

**Criticality:** **MEDIUM**
- PDF generation failure prevents report access
- Overflow errors could crash generation
- Incorrect rendering could misrepresent data

**Known Limitations:**
- Text overflow not automatically handled
- Special characters may cause rendering issues
- Large documents may have performance issues

**Mitigations:**
1. **Overflow Validation:** Truncate long text with ellipsis
2. **Error Handling:** Catch PDF generation exceptions, log failures
3. **Testing:** Test with edge cases (long text, special characters, max data)
4. **Fallback:** Raw data export available if PDF fails
5. **Version Pinning:** Use stable version, test before upgrades

**Verification:**
- ✅ Overflow handling implemented
- ✅ Edge case tests pass
- ✅ Error logging in place

**Residual Risk:** LOW (with validation and error handling)

---

### SOUP-004: psycopg2

**Component Name:** Psycopg2 PostgreSQL Adapter  
**Version:** 2.9.x  
**Vendor:** Federico Di Gregorio  
**License:** LGPL  
**Website:** https://www.psycopg.org/

**Purpose in Device:**
- Python-PostgreSQL database adapter
- Enables Django ORM to communicate with PostgreSQL
- Connection pooling

**Criticality:** **HIGH**
- Required for all database operations
- Connection failures = system unavailable
- Transaction handling critical for data integrity

**Known Limitations:**
- Connection pool exhaustion possible under high load
- Network interruptions can cause connection failures

**Mitigations:**
1. **Connection Pooling:** Configure appropriate pool size
2. **Timeout Settings:** Set reasonable connection timeouts
3. **Retry Logic:** Automatic retry for transient failures
4. **Monitoring:** Track connection pool usage

**Verification:**
- ✅ Connection pool configured
- ✅ Timeout settings reviewed

**Residual Risk:** LOW (with proper configuration)

---

### SOUP-005: Python

**Component Name:** Python Interpreter  
**Version:** 3.11.x  
**Vendor:** Python Software Foundation  
**License:** PSF License  
**Website:** https://www.python.org/

**Purpose in Device:**
- Runtime environment for entire application
- Executes all business logic
- Scoring calculations

**Criticality:** **CRITICAL**
- All code runs on Python
- Bugs in interpreter could affect calculations
- Security vulnerabilities affect entire system

**Known Limitations:**
- Floating-point arithmetic precision limitations
- Global Interpreter Lock (GIL) limits concurrency

**Mitigations:**
1. **Stable Version:** Use stable, maintained Python version
2. **Integer Arithmetic:** Use integer arithmetic for scoring (avoid floating-point)
3. **Security Updates:** Monitor Python security advisories
4. **Testing:** Comprehensive unit tests for all calculations

**Verification:**
- ✅ Scoring uses integer arithmetic only
- ✅ Unit tests verify deterministic calculations

**Residual Risk:** MINIMAL (with stable version and integer arithmetic)

---

### SOUP-006: Gunicorn

**Component Name:** Gunicorn WSGI Server  
**Version:** 20.x  
**Vendor:** Benoit Chesneau  
**License:** MIT  
**Website:** https://gunicorn.org/

**Purpose in Device:**
- Production WSGI server
- Handles HTTP requests
- Worker process management

**Criticality:** **MEDIUM**
- Server crashes = system unavailable
- Worker failures could lose in-flight requests

**Known Limitations:**
- Worker processes can crash under heavy load
- No built-in load balancing (requires reverse proxy)

**Mitigations:**
1. **Worker Configuration:** Appropriate number of workers for load
2. **Timeout Settings:** Prevent hung workers
3. **Monitoring:** Health checks and automatic restart
4. **Reverse Proxy:** Nginx for load balancing and failover

**Verification:**
- ✅ Worker configuration documented
- ✅ Health checks implemented

**Residual Risk:** LOW (with monitoring and reverse proxy)

---

### SOUP-007: Nginx

**Component Name:** Nginx Web Server  
**Version:** 1.24.x  
**Vendor:** F5, Inc.  
**License:** BSD  
**Website:** https://nginx.org/

**Purpose in Device:**
- Reverse proxy
- HTTPS termination
- Static file serving
- Load balancing

**Criticality:** **MEDIUM**
- HTTPS encryption critical for security
- Reverse proxy failure = system unavailable

**Known Limitations:**
- Configuration errors can expose system
- SSL/TLS vulnerabilities require updates

**Mitigations:**
1. **HTTPS Only:** Enforce HTTPS, redirect HTTP to HTTPS
2. **TLS Configuration:** Use modern TLS versions (1.2+)
3. **Security Headers:** HSTS, CSP, X-Frame-Options
4. **Regular Updates:** Monitor security advisories

**Verification:**
- ✅ HTTPS enforced
- ✅ Security headers configured

**Residual Risk:** LOW (with proper configuration)

---

## 3. SOUP RISK ANALYSIS SUMMARY

| SOUP ID | Component | Version | Criticality | Residual Risk | Mitigation Status |
|---------|-----------|---------|-------------|---------------|-------------------|
| SOUP-001 | Django | 4.2 LTS | HIGH | LOW | ✅ Complete |
| SOUP-002 | PostgreSQL | 14.x | CRITICAL | LOW | ✅ Complete |
| SOUP-003 | ReportLab | 3.6.x | MEDIUM | LOW | ✅ Complete |
| SOUP-004 | psycopg2 | 2.9.x | HIGH | LOW | ✅ Complete |
| SOUP-005 | Python | 3.11.x | CRITICAL | MINIMAL | ✅ Complete |
| SOUP-006 | Gunicorn | 20.x | MEDIUM | LOW | ✅ Complete |
| SOUP-007 | Nginx | 1.24.x | MEDIUM | LOW | ✅ Complete |

---

## 4. SOUP MANAGEMENT PROCEDURES

### 4.1 Version Control
- **Pinning:** All SOUP versions pinned in `requirements.txt` or infrastructure config
- **No Auto-Upgrades:** Manual review and testing required before version changes
- **Documentation:** Version changes documented with rationale

### 4.2 Security Monitoring
- **Advisories:** Monitor security mailing lists for all SOUP components
- **CVE Tracking:** Track Common Vulnerabilities and Exposures
- **Patch Management:** Apply security patches within 30 days of release
- **Testing:** Regression testing after any SOUP update

### 4.3 Change Control
Any SOUP version change requires:
1. **Risk Assessment:** Evaluate impact on device safety
2. **Testing:** Regression tests, integration tests
3. **Documentation:** Update SOUP analysis
4. **Approval:** Regulatory review for critical components

---

## 5. SOUP VALIDATION EVIDENCE

### 5.1 Django Validation
- **Transaction Safety:** Integration tests verify atomic transactions
- **Security:** Penetration testing confirms CSRF protection
- **Performance:** Load testing confirms acceptable response times

### 5.2 PostgreSQL Validation
- **Data Integrity:** Unique constraints prevent duplicate reports
- **ACID Compliance:** Transaction tests verify rollback on failure
- **Backup/Recovery:** Restore testing confirms data recovery

### 5.3 ReportLab Validation
- **PDF Generation:** Edge case tests (overflow, special characters)
- **Watermark:** Visual inspection confirms watermark placement
- **Disclaimer:** Automated test verifies disclaimer presence

---

## 6. SOUP ALTERNATIVES CONSIDERED

### 6.1 Why Django?
**Alternatives:** Flask, FastAPI
**Rationale:** Django provides:
- Mature, battle-tested framework
- Built-in ORM with transaction safety
- LTS versions with extended support
- Large community and security focus

### 6.2 Why PostgreSQL?
**Alternatives:** MySQL, SQLite
**Rationale:** PostgreSQL provides:
- Strong ACID compliance
- Advanced constraint support
- Excellent data integrity features
- Enterprise-grade reliability

### 6.3 Why ReportLab?
**Alternatives:** WeasyPrint, pdfkit
**Rationale:** ReportLab provides:
- Programmatic PDF generation
- Fine-grained layout control
- Stable, mature library
- Good documentation

---

## 7. SOUP LICENSING COMPLIANCE

| Component | License | Commercial Use | Attribution Required | Copyleft |
|-----------|---------|----------------|----------------------|----------|
| Django | BSD 3-Clause | ✅ Yes | ✅ Yes | ❌ No |
| PostgreSQL | PostgreSQL | ✅ Yes | ✅ Yes | ❌ No |
| ReportLab | BSD | ✅ Yes | ✅ Yes | ❌ No |
| psycopg2 | LGPL | ✅ Yes | ✅ Yes | ⚠️ Partial |
| Python | PSF | ✅ Yes | ✅ Yes | ❌ No |
| Gunicorn | MIT | ✅ Yes | ✅ Yes | ❌ No |
| Nginx | BSD | ✅ Yes | ✅ Yes | ❌ No |

**Compliance Status:** ✅ All licenses compatible with commercial medical device use

---

## 8. POST-MARKET SOUP MONITORING

### 8.1 Ongoing Activities
- **Security Advisories:** Weekly review of security mailing lists
- **Version Updates:** Quarterly review of available updates
- **Incident Tracking:** Log any SOUP-related failures
- **Performance Monitoring:** Track database, web server performance

### 8.2 Update Triggers
- **Security Vulnerability:** Immediate assessment and patching
- **Bug Fix:** Evaluate impact, test, and apply if relevant
- **Feature Update:** Defer unless needed for device functionality
- **End of Life:** Plan migration before EOL date

---

## DOCUMENT CONTROL

**Prepared By:** Software Engineering / Regulatory Affairs  
**Reviewed By:** [To be completed]  
**Approved By:** [To be completed]  
**Effective Date:** 2026-02-14  
**Next Review:** Quarterly or upon SOUP change

---

**END OF DOCUMENT**
