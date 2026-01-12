import json
import os
from django.utils import timezone
from backend.clinical.models import BatterySession, TestRun


def load_battery_registry():
    path = os.path.join(os.path.dirname(__file__), "battery_registry.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_battery_def(battery_code: str):
    reg = load_battery_registry()
    for b in reg:
        if b["battery_code"] == battery_code:
            return b
    raise ValueError(f"Unknown battery_code: {battery_code}")


def start_session(session: BatterySession):
    if session.status != "NOT_STARTED":
        return session
    session.status = "IN_PROGRESS"
    session.started_at = timezone.now()
    session.current_test_index = 0
    session.save(update_fields=["status", "started_at", "current_test_index"])
    return session


def get_current_test_code(session: BatterySession) -> str:
    battery = get_battery_def(session.order.battery_code)
    idx = session.current_test_index
    tests = battery["tests"]
    if idx < 0 or idx >= len(tests):
        raise ValueError("current_test_index out of range")
    return tests[idx]


def open_current_test_run(session: BatterySession) -> TestRun:
    test_code = get_current_test_code(session)

    tr = TestRun.objects.filter(
        session=session,
        test_order_index=session.current_test_index
    ).first()

    if tr:
        return tr

    tr = TestRun.objects.create(
        organization_id=session.organization_id,
        session=session,
        test_code=test_code,
        test_order_index=session.current_test_index,
        time_started=timezone.now(),
    )
    return tr


def advance_to_next_test(session: BatterySession):
    battery = get_battery_def(session.order.battery_code)
    total = len(battery["tests"])

    if session.current_test_index < total - 1:
        session.current_test_index += 1
        session.save(update_fields=["current_test_index"])
        return False  # not completed

    session.status = "COMPLETED"
    session.completed_at = timezone.now()
    session.save(update_fields=["status", "completed_at"])
    return True  # completed
