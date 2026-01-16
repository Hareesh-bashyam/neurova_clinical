import json
from apps.clinical_ops.models_assessment import AssessmentResponse, AssessmentResult
from apps.clinical_ops.models_report import AssessmentReport

def export_order_data(order):
    payload = {
        "order_id": order.id,
        "battery": order.battery_code,
        "created_at": order.created_at.isoformat(),
        "deletion_status": order.deletion_status,
        "response": None,
        "result": None,
        "report": None,
    }

    if order.deletion_status != "DELETED":
        r = AssessmentResponse.objects.filter(order=order).first()
        if r:
            payload["response"] = r.answers_json

        res = AssessmentResult.objects.filter(order=order).first()
        if res:
            payload["result"] = res.result_json

        rep = AssessmentReport.objects.filter(order=order).first()
        if rep:
            payload["report"] = {
                "signoff_status": rep.signoff_status,
                "signed_by": rep.signed_by_name,
                "signed_at": rep.signed_at.isoformat() if rep.signed_at else None,
            }

    return json.dumps(payload, ensure_ascii=False, indent=2)
