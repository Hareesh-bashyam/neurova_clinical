import random
from django.utils import timezone


def generate_code() -> str:
    return f"{random.randint(100000, 999999)}"


def issue_report_access_code(order, minutes_valid=15):
    code = generate_code()
    order.report_access_code = code
    order.report_access_code_expires_at = timezone.now() + timezone.timedelta(minutes=minutes_valid)
    order.save(update_fields=["report_access_code", "report_access_code_expires_at"])
    return code


def verify_report_access_code(order, code: str) -> bool:
    if not order.report_access_code or not order.report_access_code_expires_at:
        return False
    if timezone.now() > order.report_access_code_expires_at:
        return False
    return str(code) == str(order.report_access_code)
