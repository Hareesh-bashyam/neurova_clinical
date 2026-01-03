from io import BytesIO
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def generate_report_pdf(report):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)

    data = report.report_json
    y = 800

    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, "Clinical Assessment Report")
    y -= 40

    p.setFont("Helvetica", 11)
    p.drawString(50, y, f"Session ID: {data.get('session_id')}")
    y -= 20

    p.drawString(50, y, f"Instrument: {data.get('instrument')}")
    y -= 20

    p.drawString(50, y, f"Score: {data.get('score')}")
    y -= 20

    p.drawString(50, y, f"Severity: {data.get('severity')}")
    y -= 30

    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Answers")
    y -= 20

    p.setFont("Helvetica", 10)
    for q, a in data.get("answers", {}).items():
        p.drawString(60, y, f"{q}: {a}")
        y -= 15

        if y < 50:
            p.showPage()
            y = 800

    p.showPage()
    p.save()

    buffer.seek(0)

    filename = f"report_{report.id}.pdf"
    report.pdf_file.save(filename, ContentFile(buffer.read()))
    report.save(update_fields=["pdf_file"])
