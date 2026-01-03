from .models import Instrument, TestDefinition, Panel, PanelItem

def import_catalog(org, data: dict):
    """
    Deterministic catalog import.
    Must be idempotent at org level.
    """

    # 1️⃣ Instruments
    for inst in data.get("instruments", []):
        Instrument.objects.get_or_create(
            organization=org,
            code=inst["code"],
            version=inst["version"],
            defaults={
                "name": inst["name"],
                "owner": inst.get("owner", ""),
                "license_type": inst.get("license_type", "UNKNOWN"),
                "commercial_use_allowed": inst.get("commercial_use_allowed", "UNKNOWN"),
                "source_url": inst.get("source_url", ""),
                "notes": inst.get("notes", ""),
            },
        )

    # 2️⃣ Test Definitions
    for test in data.get("tests", []):
        instrument = Instrument.objects.get(
            organization=org,
            code=test["instrument"],
            version=test["instrument_version"],
        )

        TestDefinition.objects.get_or_create(
            organization=org,
            instrument=instrument,
            code=test["code"],
            version=test["version"],
            language=test.get("language", "en"),
            defaults={
                "name": test["name"],
                "json_schema": test["json_schema"],
                "scoring_spec": test["scoring_spec"],
                "is_active": True,
            },
        )

    # 3️⃣ Panels
    for panel in data.get("panels", []):
        p, _ = Panel.objects.get_or_create(
            organization=org,
            code=panel["code"],
            defaults={
                "name": panel["name"],
                "description": panel.get("description", ""),
            },
        )

        for idx, test_code in enumerate(panel["tests"]):
            test = TestDefinition.objects.get(
                organization=org,
                code=test_code,
            )

            PanelItem.objects.get_or_create(
                organization=org,
                panel=p,
                test=test,
                defaults={"order_index": idx},
            )
