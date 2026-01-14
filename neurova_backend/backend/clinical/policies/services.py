from .models import OrgClinicalPolicy
from backend.clinical.batteries.battery_runner import load_battery_registry

def get_or_create_policy(org_id):
    pol = OrgClinicalPolicy.objects.filter(organization_id=org_id).first()
    if pol:
        return pol
    reg = load_battery_registry()
    all_codes = [b["battery_code"] for b in reg]
    return OrgClinicalPolicy.objects.create(
        organization_id=org_id,
        enabled_batteries=all_codes,
        signoff_required_global=False
    )

def battery_enabled(pol, battery_code):
    return battery_code in (pol.enabled_batteries or [])

