"""
Django management command to run PMS queries
Usage: python manage.py run_pms_metrics
"""

from django.core.management.base import BaseCommand
from django.db.models import Count, Avg, Q, F, ExpressionWrapper, fields
from django.db.models.functions import TruncQuarter
from datetime import datetime

from apps.clinical_ops.models import AssessmentOrder
from apps.clinical_ops.models_report import AssessmentReport
from apps.clinical_ops.models_assessment import AssessmentResult
from apps.clinical_ops.audit.models import AuditEvent
from apps.clinical_ops.models import ResponseQuality


class Command(BaseCommand):
    help = 'Run Post-Market Surveillance metrics queries'

    def handle(self, *args, **options):
        self.stdout.write("="*80)
        self.stdout.write("POST-MARKET SURVEILLANCE METRICS")
        self.stdout.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write("="*80)
        
        start_date = datetime(2026, 1, 1)
        
        # METRIC 1: Total Assessments Started
        self.stdout.write("\n" + "="*80)
        self.stdout.write("METRIC 1: Total Assessments Started")
        self.stdout.write("="*80)
        
        try:
            assessments = AssessmentOrder.objects.filter(
                created_at__gte=start_date,
                deletion_status='ACTIVE'
            ).annotate(
                quarter=TruncQuarter('created_at')
            ).values('quarter').annotate(
                total=Count('id')
            ).order_by('-quarter')
            
            for row in assessments:
                self.stdout.write(f"Quarter: {row['quarter']} | Total: {row['total']}")
            
            if not assessments:
                self.stdout.write("No data available")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
        
        # METRIC 2: Abandonment Rate
        self.stdout.write("\n" + "="*80)
        self.stdout.write("METRIC 2: Abandonment Rate")
        self.stdout.write("="*80)
        
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
                self.stdout.write(f"Quarter: {row['quarter']} | Total: {total} | Abandoned: {abandoned} | Rate: {rate:.2f}%")
            
            if not abandonment:
                self.stdout.write("No data available")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
        
        # SUMMARY
        self.stdout.write("\n" + "="*80)
        self.stdout.write("SUMMARY STATISTICS")
        self.stdout.write("="*80)
        
        try:
            total_orders = AssessmentOrder.objects.filter(deletion_status='ACTIVE').count()
            total_completed = AssessmentOrder.objects.filter(
                status__in=['COMPLETED', 'AWAITING_REVIEW', 'DELIVERED'],
                deletion_status='ACTIVE'
            ).count()
            total_reports = AssessmentReport.objects.count()
            total_audit_events = AuditEvent.objects.count()
            
            self.stdout.write(f"Total Orders: {total_orders}")
            self.stdout.write(f"Total Completed: {total_completed}")
            self.stdout.write(f"Total Reports: {total_reports}")
            self.stdout.write(f"Total Audit Events: {total_audit_events}")
            
            if total_orders > 0:
                completion_rate = (total_completed / total_orders * 100)
                self.stdout.write(f"Completion Rate: {completion_rate:.2f}%")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
        
        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.SUCCESS("PMS Metrics Report Complete"))
        self.stdout.write("="*80)
