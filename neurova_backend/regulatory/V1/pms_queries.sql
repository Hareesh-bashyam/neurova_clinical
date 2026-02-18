-- POST-MARKET SURVEILLANCE QUERIES (UPDATED FOR ACTUAL MODELS)
-- Neurova Clinical Engine V1
-- Purpose: Derive PMS metrics from existing database tables
-- Version: 1.1 (Updated with actual model names)
-- Date: 2026-02-14

-- ============================================================================
-- ACTUAL MODEL MAPPING
-- ============================================================================
-- Order Model: apps_clinical_ops_assessmentorder
-- Audit Model: apps_clinical_ops_audit_auditevent
-- Report Model: apps_clinical_ops_assessmentreport
-- Patient Model: apps_clinical_ops_patient
-- Response Quality: apps_clinical_ops_responsequality

-- ============================================================================
-- METRIC 1: Total Assessments Started
-- ============================================================================
-- Description: Count of all orders created (screening initiated)
-- Table: apps_clinical_ops_assessmentorder
-- Frequency: Run quarterly

SELECT 
    COUNT(*) as total_assessments_started,
    DATE_TRUNC('quarter', created_at) as quarter
FROM apps_clinical_ops_assessmentorder
WHERE created_at >= '2026-01-01'  -- Adjust date range as needed
  AND deletion_status = 'ACTIVE'  -- Exclude deleted records
GROUP BY DATE_TRUNC('quarter', created_at)
ORDER BY quarter DESC;

-- ============================================================================
-- METRIC 2: Total Assessments Completed
-- ============================================================================
-- Description: Count of orders with status = 'COMPLETED' or 'AWAITING_REVIEW' or 'DELIVERED'
-- Table: apps_clinical_ops_assessmentorder
-- Frequency: Run quarterly

SELECT 
    COUNT(*) as total_assessments_completed,
    DATE_TRUNC('quarter', created_at) as quarter
FROM apps_clinical_ops_assessmentorder
WHERE status IN ('COMPLETED', 'AWAITING_REVIEW', 'DELIVERED')
  AND created_at >= '2026-01-01'
  AND deletion_status = 'ACTIVE'
GROUP BY DATE_TRUNC('quarter', created_at)
ORDER BY quarter DESC;

-- ============================================================================
-- METRIC 3: Abandonment Rate
-- ============================================================================
-- Description: Percentage of orders started but not completed
-- Tables: apps_clinical_ops_assessmentorder
-- Formula: (Orders with status CREATED or IN_PROGRESS / Total orders) * 100
-- Frequency: Run quarterly

SELECT 
    DATE_TRUNC('quarter', created_at) as quarter,
    COUNT(*) as total_started,
    SUM(CASE WHEN status IN ('CREATED', 'IN_PROGRESS') THEN 1 ELSE 0 END) as abandoned,
    ROUND(
        (SUM(CASE WHEN status IN ('CREATED', 'IN_PROGRESS') THEN 1 ELSE 0 END)::DECIMAL / COUNT(*)) * 100, 
        2
    ) as abandonment_rate_percent
FROM apps_clinical_ops_assessmentorder
WHERE created_at >= '2026-01-01'
  AND deletion_status = 'ACTIVE'
GROUP BY DATE_TRUNC('quarter', created_at)
ORDER BY quarter DESC;

-- ============================================================================
-- METRIC 4: Red Flag Frequency
-- ============================================================================
-- Description: Count and percentage of orders with critical red flags
-- Table: apps_clinical_ops_assessmentresult (assuming red_flag field exists)
-- Note: Adjust based on actual red flag detection implementation
-- Frequency: Run quarterly

-- Option A: If red flags stored in AssessmentResult
SELECT 
    DATE_TRUNC('quarter', o.created_at) as quarter,
    COUNT(DISTINCT o.id) as total_completed,
    COUNT(DISTINCT CASE WHEN r.severity = 'CRITICAL' THEN o.id END) as red_flag_count,
    ROUND(
        (COUNT(DISTINCT CASE WHEN r.severity = 'CRITICAL' THEN o.id END)::DECIMAL / COUNT(DISTINCT o.id)) * 100,
        2
    ) as red_flag_rate_percent
FROM apps_clinical_ops_assessmentorder o
LEFT JOIN apps_clinical_ops_assessmentresult r ON r.order_id = o.id
WHERE o.status IN ('COMPLETED', 'AWAITING_REVIEW', 'DELIVERED')
  AND o.created_at >= '2026-01-01'
  AND o.deletion_status = 'ACTIVE'
GROUP BY DATE_TRUNC('quarter', o.created_at)
ORDER BY quarter DESC;

-- Option B: If red flags tracked via audit events
SELECT 
    DATE_TRUNC('quarter', created_at) as quarter,
    COUNT(DISTINCT entity_id) as orders_with_red_flags
FROM apps_clinical_ops_audit_auditevent
WHERE event_type = 'RED_FLAG_DETECTED'
  AND created_at >= '2026-01-01'
GROUP BY DATE_TRUNC('quarter', created_at)
ORDER BY quarter DESC;

-- ============================================================================
-- METRIC 5: Report Generation Count
-- ============================================================================
-- Description: Count of PDF reports generated
-- Table: apps_clinical_ops_assessmentreport
-- Frequency: Run quarterly

SELECT 
    DATE_TRUNC('quarter', generated_at) as quarter,
    COUNT(*) as pdf_reports_generated
FROM apps_clinical_ops_assessmentreport
WHERE generated_at >= '2026-01-01'
GROUP BY DATE_TRUNC('quarter', generated_at)
ORDER BY quarter DESC;

-- Alternative: Count via audit events
SELECT 
    DATE_TRUNC('quarter', created_at) as quarter,
    COUNT(*) as pdf_reports_generated
FROM apps_clinical_ops_audit_auditevent
WHERE event_type = 'PDF_GENERATED'
  AND created_at >= '2026-01-01'
GROUP BY DATE_TRUNC('quarter', created_at)
ORDER BY quarter DESC;

-- ============================================================================
-- METRIC 6: Average Time to Clinician Review
-- ============================================================================
-- Description: Average time from order completion to report sign-off
-- Tables: apps_clinical_ops_assessmentorder, apps_clinical_ops_assessmentreport
-- Frequency: Run quarterly

SELECT 
    DATE_TRUNC('quarter', o.created_at) as quarter,
    COUNT(*) as reviewed_orders,
    ROUND(
        AVG(EXTRACT(EPOCH FROM (r.signed_at - o.completed_at)) / 3600)::NUMERIC,
        2
    ) as avg_hours_to_review,
    ROUND(
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (r.signed_at - o.completed_at)) / 3600)::NUMERIC,
        2
    ) as median_hours_to_review
FROM apps_clinical_ops_assessmentorder o
INNER JOIN apps_clinical_ops_assessmentreport r ON r.order_id = o.id
WHERE r.signoff_status = 'SIGNED'
  AND r.signed_at IS NOT NULL
  AND o.completed_at IS NOT NULL
  AND o.created_at >= '2026-01-01'
  AND o.deletion_status = 'ACTIVE'
GROUP BY DATE_TRUNC('quarter', o.created_at)
ORDER BY quarter DESC;

-- ============================================================================
-- METRIC 7: Red Flag Review Time (Critical)
-- ============================================================================
-- Description: Time to review for orders with critical red flags
-- Target: <24 hours for critical flags
-- Frequency: Run monthly

SELECT 
    DATE_TRUNC('month', o.created_at) as month,
    COUNT(*) as critical_flag_orders,
    ROUND(
        AVG(EXTRACT(EPOCH FROM (r.signed_at - o.completed_at)) / 3600)::NUMERIC,
        2
    ) as avg_hours_to_review,
    SUM(CASE 
        WHEN EXTRACT(EPOCH FROM (r.signed_at - o.completed_at)) / 3600 > 24 
        THEN 1 ELSE 0 
    END) as reviews_exceeding_24hrs
FROM apps_clinical_ops_assessmentorder o
INNER JOIN apps_clinical_ops_assessmentreport r ON r.order_id = o.id
INNER JOIN apps_clinical_ops_assessmentresult res ON res.order_id = o.id
WHERE res.severity = 'CRITICAL'
  AND r.signoff_status = 'SIGNED'
  AND r.signed_at IS NOT NULL
  AND o.created_at >= '2026-01-01'
  AND o.deletion_status = 'ACTIVE'
GROUP BY DATE_TRUNC('month', o.created_at)
ORDER BY month DESC;

-- ============================================================================
-- METRIC 8: Instrument Distribution
-- ============================================================================
-- Description: Breakdown of which screening instruments are being used
-- Table: apps_clinical_ops_assessmentorder
-- Field: battery_code, battery_version
-- Frequency: Run quarterly

SELECT 
    DATE_TRUNC('quarter', created_at) as quarter,
    battery_code,
    battery_version,
    COUNT(*) as usage_count,
    ROUND(
        (COUNT(*)::DECIMAL / SUM(COUNT(*)) OVER (PARTITION BY DATE_TRUNC('quarter', created_at))) * 100,
        2
    ) as percentage
FROM apps_clinical_ops_assessmentorder
WHERE created_at >= '2026-01-01'
  AND deletion_status = 'ACTIVE'
GROUP BY DATE_TRUNC('quarter', created_at), battery_code, battery_version
ORDER BY quarter DESC, usage_count DESC;

-- ============================================================================
-- METRIC 9: Completion Rate by Time of Day
-- ============================================================================
-- Description: Identify if certain times have higher abandonment
-- Useful for usability insights
-- Frequency: Run quarterly

SELECT 
    EXTRACT(HOUR FROM created_at) as hour_of_day,
    COUNT(*) as total_started,
    SUM(CASE WHEN status NOT IN ('CREATED', 'IN_PROGRESS') THEN 1 ELSE 0 END) as completed,
    ROUND(
        (SUM(CASE WHEN status NOT IN ('CREATED', 'IN_PROGRESS') THEN 1 ELSE 0 END)::DECIMAL / COUNT(*)) * 100,
        2
    ) as completion_rate_percent
FROM apps_clinical_ops_assessmentorder
WHERE created_at >= '2026-01-01'
  AND deletion_status = 'ACTIVE'
GROUP BY EXTRACT(HOUR FROM created_at)
ORDER BY hour_of_day;

-- ============================================================================
-- METRIC 10: Response Quality Flags
-- ============================================================================
-- Description: Track response quality issues (too fast, straight-lining, etc.)
-- Table: apps_clinical_ops_responsequality
-- Frequency: Run quarterly

SELECT 
    DATE_TRUNC('quarter', rq.created_at) as quarter,
    COUNT(*) as total_assessments,
    SUM(CASE WHEN rq.too_fast_flag = TRUE THEN 1 ELSE 0 END) as too_fast_count,
    SUM(CASE WHEN rq.straight_lining_flag = TRUE THEN 1 ELSE 0 END) as straight_lining_count,
    SUM(CASE WHEN rq.inconsistency_flag = TRUE THEN 1 ELSE 0 END) as inconsistency_count,
    ROUND(AVG(rq.duration_seconds)::NUMERIC, 2) as avg_duration_seconds
FROM apps_clinical_ops_responsequality rq
INNER JOIN apps_clinical_ops_assessmentorder o ON o.id = rq.order_id
WHERE rq.created_at >= '2026-01-01'
  AND o.deletion_status = 'ACTIVE'
GROUP BY DATE_TRUNC('quarter', rq.created_at)
ORDER BY quarter DESC;

-- ============================================================================
-- METRIC 11: Audit Event Summary
-- ============================================================================
-- Description: Summary of all audit events by type
-- Table: apps_clinical_ops_audit_auditevent
-- Frequency: Run quarterly

SELECT 
    DATE_TRUNC('quarter', created_at) as quarter,
    event_type,
    COUNT(*) as event_count,
    COUNT(DISTINCT entity_id) as unique_entities
FROM apps_clinical_ops_audit_auditevent
WHERE created_at >= '2026-01-01'
GROUP BY DATE_TRUNC('quarter', created_at), event_type
ORDER BY quarter DESC, event_count DESC;

-- ============================================================================
-- METRIC 12: Delivery Mode Distribution
-- ============================================================================
-- Description: How are reports being delivered to patients
-- Table: apps_clinical_ops_assessmentorder
-- Frequency: Run quarterly

SELECT 
    DATE_TRUNC('quarter', created_at) as quarter,
    delivery_mode,
    COUNT(*) as count,
    ROUND(
        (COUNT(*)::DECIMAL / SUM(COUNT(*)) OVER (PARTITION BY DATE_TRUNC('quarter', created_at))) * 100,
        2
    ) as percentage
FROM apps_clinical_ops_assessmentorder
WHERE status = 'DELIVERED'
  AND created_at >= '2026-01-01'
  AND deletion_status = 'ACTIVE'
GROUP BY DATE_TRUNC('quarter', created_at), delivery_mode
ORDER BY quarter DESC, count DESC;

-- ============================================================================
-- USAGE INSTRUCTIONS
-- ============================================================================
-- 1. Run these queries quarterly as part of PMS review
-- 2. Export results to CSV for regulatory documentation
-- 3. Compare results to baseline (first 6 months)
-- 4. Flag any metrics exceeding thresholds:
--    - Abandonment rate >10%
--    - Red flag review time >24 hours
--    - Red flag frequency >50% increase from baseline
--    - Response quality flags >15%
-- 5. Document findings in quarterly PMS report
-- 6. Escalate anomalies to regulatory affairs team

-- ============================================================================
-- NOTES
-- ============================================================================
-- - Table names use Django's default naming: app_model format with underscores
-- - Adjust field names if they differ in actual implementation
-- - These queries assume PostgreSQL syntax
-- - For production use, consider creating views for frequently-run queries
-- - Ensure queries are optimized with appropriate indexes
-- - Red flag detection logic may need adjustment based on actual implementation

-- END OF PMS QUERIES
