from django.utils import timezone

DEFAULT_RETENTION_DAYS = 365 * 5  # 5 years (India medical records norm)

def compute_retention_date(created_at, days=DEFAULT_RETENTION_DAYS):
    return created_at + timezone.timedelta(days=days)

