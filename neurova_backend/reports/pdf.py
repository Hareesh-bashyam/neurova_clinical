from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime


def generate_report_pdf(path, context):
    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4

    y = height - 40

    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "Psychiatric Screening & Assessment Report")
    y -= 30

    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Patient: {context.get('patient_name', '')}")
    y -= 15
    c.drawString(40, y, f"Session ID: {context.get('session_id')}")
    y -= 15
    c.drawString(40, y, f"Generated At: {datetime.utcnow().isoformat()} UTC")
    y -= 20

    for test in context.get("tests", []):
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, y, f"{test['code']}")
        y -= 12
        c.setFont("Helvetica", 10)
        c.drawString(60, y, f"Score: {test['score']} | Severity: {test['severity']}")
        y -= 15

    if context.get("critical_self_harm"):
        y -= 10
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, y, "Critical Alert:")
        y -= 12
        c.setFont("Helvetica", 10)
        c.drawString(
            40,
            y,
            "Critical Alert: Patient has reported thoughts of self-harm. Immediate clinical assessment is mandatory. "
            "This software does not provide real-time monitoring. Tele-MANAS: 14416."
        )
        y -= 20

    y -= 20
    c.setFont("Helvetica", 8)
    c.drawString(
        40,
        y,
        "This report is generated from standardized psychometric instruments and is intended to assist "
        "qualified healthcare professionals. It is not a medical diagnosis. Final clinical interpretation "
        "must be made by a registered practitioner."
    )

    y -= 15
    c.drawString(40, y, f"Engine Version: {context.get('engine_version')}")
    y -= 12
    c.drawString(40, y, f"Report Schema Version: {context.get('report_schema_version')}")

    c.showPage()
    c.save()
