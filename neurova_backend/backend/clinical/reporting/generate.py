from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings

from core.models import Organization
from backend.clinical.scoring.engine_v1 import score_phq9
from backend.clinical.reporting.report_schema_v1 import empty_report
from backend.clinical.reporting.report_builder_v1 import (
    generate_report_for_order_v1 as _canonical_generate_report_for_order_v1
)


def generate_report_for_order_v1(order):
    """
    Canonical V1 report generator.
    Populates ALL mandatory blocks required by the PDF composer.
    """
    return _canonical_generate_report_for_order_v1(order)
