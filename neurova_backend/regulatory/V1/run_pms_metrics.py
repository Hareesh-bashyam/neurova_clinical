"""
Post-Market Surveillance Metrics Script
Executes PMS queries and outputs results for regulatory documentation
"""

import os
import sys
import django
from datetime import datetime, timedelta
from django.db.models import Count, Avg, Q, F, ExpressionWrapper, fields
from django.db.models.functions import TruncQuarter, TruncMonth, TruncHour, Extract
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neurova_backend.settings')
django.setup()

from apps.clinical_ops.models import AssessmentOrder, Patient
from apps.clinical_ops.models_report import AssessmentReport
from apps.clinical_ops.models_assessment import AssessmentResult
from apps.clinical_ops.audit.models import AuditEvent
from apps.clinical_ops.models import ResponseQuality

print("="*80)
print("POST-MARKET SURVEILLANCE METRICS")
print("Neurova Clinical Engine V1")
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)
print()

# Date range for queries
start_date = datetime(2026, 1, 1)

# ============================================================================
# METRIC 1: Total Assessments Started
# ============================================================================
print("\n" + "="*80)
print("METRIC 1: Total Assessments Started (Quarterly)")
print("="*80)

try:
    assessments_started = AssessmentOrder.objects.filter(
        created_at__gte=start_date,
        deletion_status='ACTIVE'
    ).annotate(
        quarter=TruncQuarter('created_at')
    ).values('quarter').annotate(
        total=Count('id')
    ).order_by('-quarter')
    
    for row in assessments_started:
        print(f"Quarter: {row['quarter'].strftime('%Y-Q%q')} | Total Started: {row['total']}")
    
    if not assessments_started:
        print("No data available")
except Exception as e:
    print(f"Error: {e}")

# ============================================================================
# METRIC 2: Total Assessments Completed
# ============================================================================
print("\n" + "="*80)
print("METRIC 2: Total Assessments Completed (Quarterly)")
print("="*80)

try:
    assessments_completed = AssessmentOrder.objects.filter(
        status__in=['COMPLETED', 'AWAITING_REVIEW', 'DELIVERED'],
        created_at__gte=start_date,
        deletion_status='ACTIVE'
    ).annotate(
        quarter=TruncQuarter('created_at')
    ).values('quarter').annotate(
        total=Count('id')
    ).order_by('-quarter')
    
    for row in assessments_completed:
        print(f"Quarter: {row['quarter'].strftime('%Y-Q%q')} | Total Completed: {row['total']}")
    
    if not assessments_completed:
        print("No data available")
except Exception as e:
    print(f"Error: {e}")

# ============================================================================
# METRIC 3: Abandonment Rate
# ============================================================================
print("\n" + "="*80)
print("METRIC 3: Abandonment Rate (Quarterly)")
print("="*80)

try:
    abandonment = AssessmentOrder.objects.filter(
        created_at__gte=start_date,
        deletion_status='ACTIVE'
    ).annotate(
        quarter=TruncQuarter('created_at')
    ).values('quarter').annotate(
        total_started=Count('id'),
        abandoned=Count('id', filter=Q(status__in=['CREATED', 'IN_PROGRESS']))
    ).order_by('-quarter')
    
    for row in abandonment:
        total = row['total_started']
        abandoned = row['abandoned']
        rate = (abandoned / total * 100) if total > 0 else 0
        print(f"Quarter: {row['quarter'].strftime('%Y-Q%q')} | Total: {total} | Abandoned: {abandoned} | Rate: {rate:.2f}%")
    
    if not abandonment:
        print("No data available")
except Exception as e:
    print(f"Error: {e}")

# ============================================================================
# METRIC 4: Red Flag Frequency
# ============================================================================
print("\n" + "="*80)
print("METRIC 4: Red Flag Frequency (Quarterly)")
print("="*80)

try:
    red_flags = AssessmentOrder.objects.filter(
        status__in=['COMPLETED', 'AWAITING_REVIEW', 'DELIVERED'],
        created_at__gte=start_date,
        deletion_status='ACTIVE'
    ).annotate(
        quarter=TruncQuarter('created_at')
    ).values('quarter').annotate(
        total_completed=Count('id'),
        red_flag_count=Count('id', filter=Q(result__has_red_flags=True))
    ).order_by('-quarter')
    
    for row in red_flags:
        total = row['total_completed']
        flags = row['red_flag_count']
        rate = (flags / total * 100) if total > 0 else 0
        print(f"Quarter: {row['quarter'].strftime('%Y-Q%q')} | Completed: {total} | Red Flags: {flags} | Rate: {rate:.2f}%")
    
    if not red_flags:
        print("No data available")
except Exception as e:
    print(f"Error: {e}")

# ============================================================================
# METRIC 5: Report Generation Count
# ============================================================================
print("\n" + "="*80)
print("METRIC 5: PDF Reports Generated (Quarterly)")
print("="*80)

try:
    reports_generated = AssessmentReport.objects.filter(
        generated_at__gte=start_date
    ).annotate(
        quarter=TruncQuarter('generated_at')
    ).values('quarter').annotate(
        total=Count('id')
    ).order_by('-quarter')
    
    for row in reports_generated:
        print(f"Quarter: {row['quarter'].strftime('%Y-Q%q')} | Reports Generated: {row['total']}")
    
    if not reports_generated:
        print("No data available")
except Exception as e:
    print(f"Error: {e}")

# ============================================================================
# METRIC 6: Average Time to Clinician Review
# ============================================================================
print("\n" + "="*80)
print("METRIC 6: Average Time to Clinician Review (Quarterly)")
print("="*80)

try:
    review_times = AssessmentOrder.objects.filter(
        created_at__gte=start_date,
        deletion_status='ACTIVE',
        completed_at__isnull=False,
        report__signoff_status='SIGNED',
        report__signed_at__isnull=False
    ).annotate(
        quarter=TruncQuarter('created_at'),
        review_hours=ExpressionWrapper(
            (F('report__signed_at') - F('completed_at')),
            output_field=fields.DurationField()
        )
    ).values('quarter').annotate(
        reviewed_orders=Count('id'),
        avg_hours=Avg('review_hours')
    ).order_by('-quarter')
    
    for row in review_times:
        avg_hours = row['avg_hours'].total_seconds() / 3600 if row['avg_hours'] else 0
        print(f"Quarter: {row['quarter'].strftime('%Y-Q%q')} | Reviewed: {row['reviewed_orders']} | Avg Hours: {avg_hours:.2f}")
    
    if not review_times:
        print("No data available")
except Exception as e:
    print(f"Error: {e}")

# ============================================================================
# METRIC 7: Instrument Distribution
# ============================================================================
print("\n" + "="*80)
print("METRIC 7: Instrument Distribution (Quarterly)")
print("="*80)

try:
    instruments = AssessmentOrder.objects.filter(
        created_at__gte=start_date,
        deletion_status='ACTIVE'
    ).annotate(
        quarter=TruncQuarter('created_at')
    ).values('quarter', 'battery_code', 'battery_version').annotate(
        usage_count=Count('id')
    ).order_by('-quarter', '-usage_count')
    
    for row in instruments:
        print(f"Quarter: {row['quarter'].strftime('%Y-Q%q')} | Battery: {row['battery_code']} v{row['battery_version']} | Count: {row['usage_count']}")
    
    if not instruments:
        print("No data available")
except Exception as e:
    print(f"Error: {e}")

# ============================================================================
# METRIC 8: Response Quality Flags
# ============================================================================
print("\n" + "="*80)
print("METRIC 8: Response Quality Flags (Quarterly)")
print("="*80)

try:
    quality_flags = ResponseQuality.objects.filter(
        created_at__gte=start_date,
        order__deletion_status='ACTIVE'
    ).annotate(
        quarter=TruncQuarter('created_at')
    ).values('quarter').annotate(
        total=Count('id'),
        too_fast=Count('id', filter=Q(too_fast_flag=True)),
        straight_lining=Count('id', filter=Q(straight_lining_flag=True)),
        inconsistency=Count('id', filter=Q(inconsistency_flag=True)),
        avg_duration=Avg('duration_seconds')
    ).order_by('-quarter')
    
    for row in quality_flags:
        print(f"Quarter: {row['quarter'].strftime('%Y-Q%q')}")
        print(f"  Total: {row['total']}")
        print(f"  Too Fast: {row['too_fast']}")
        print(f"  Straight Lining: {row['straight_lining']}")
        print(f"  Inconsistency: {row['inconsistency']}")
        print(f"  Avg Duration: {row['avg_duration']:.2f}s")
    
    if not quality_flags:
        print("No data available")
except Exception as e:
    print(f"Error: {e}")

# ============================================================================
# METRIC 9: Audit Event Summary
# ============================================================================
print("\n" + "="*80)
print("METRIC 9: Audit Event Summary (Top 10 Event Types)")
print("="*80)

try:
    audit_summary = AuditEvent.objects.filter(
        created_at__gte=start_date
    ).values('event_type').annotate(
        event_count=Count('id'),
        unique_entities=Count('entity_id', distinct=True)
    ).order_by('-event_count')[:10]
    
    for row in audit_summary:
        print(f"Event: {row['event_type']:30s} | Count: {row['event_count']:6d} | Unique Entities: {row['unique_entities']}")
    
    if not audit_summary:
        print("No data available")
except Exception as e:
    print(f"Error: {e}")

# ============================================================================
# METRIC 10: Delivery Mode Distribution
# ============================================================================
print("\n" + "="*80)
print("METRIC 10: Delivery Mode Distribution (Quarterly)")
print("="*80)

try:
    delivery_modes = AssessmentOrder.objects.filter(
        status='DELIVERED',
        created_at__gte=start_date,
        deletion_status='ACTIVE'
    ).annotate(
        quarter=TruncQuarter('created_at')
    ).values('quarter', 'delivery_mode').annotate(
        count=Count('id')
    ).order_by('-quarter', '-count')
    
    for row in delivery_modes:
        print(f"Quarter: {row['quarter'].strftime('%Y-Q%q')} | Mode: {row['delivery_mode']} | Count: {row['count']}")
    
    if not delivery_modes:
        print("No data available")
except Exception as e:
    print(f"Error: {e}")

# ============================================================================
# SUMMARY STATISTICS
# ============================================================================
print("\n" + "="*80)
print("SUMMARY STATISTICS (All Time)")
print("="*80)

try:
    total_orders = AssessmentOrder.objects.filter(deletion_status='ACTIVE').count()
    total_completed = AssessmentOrder.objects.filter(
        status__in=['COMPLETED', 'AWAITING_REVIEW', 'DELIVERED'],
        deletion_status='ACTIVE'
    ).count()
    total_reports = AssessmentReport.objects.count()
    total_audit_events = AuditEvent.objects.count()
    
    print(f"Total Orders: {total_orders}")
    print(f"Total Completed: {total_completed}")
    print(f"Total Reports Generated: {total_reports}")
    print(f"Total Audit Events: {total_audit_events}")
    
    if total_orders > 0:
        completion_rate = (total_completed / total_orders * 100)
        print(f"Overall Completion Rate: {completion_rate:.2f}%")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*80)
print("END OF PMS METRICS REPORT")
print("="*80)
