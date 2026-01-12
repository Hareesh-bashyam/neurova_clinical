from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from backend.clinical.reporting.report_sections_v1 import compose_sections_v1


def render_pdf_from_report_json_v1(report_json):
    """
    Renders a PDF from frozen report_json.
    MUST NOT recompute scores or modify report_json.
    """

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    width, height = A4
    y = height - 40

    sections = compose_sections_v1(report_json)

    for section in sections:
        # Title
        if section.title:
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(40, y, section.title)
            y -= 18

        # Lines
        pdf.setFont("Helvetica", 10)
        for line in section.lines:
            if y < 40:
                pdf.showPage()
                y = height - 40
                pdf.setFont("Helvetica", 10)

            pdf.drawString(40, y, line)
            y -= 14

        # Simple table rendering (minimal V1)
        if section.table:
            headers = section.table.get("headers", [])
            rows = section.table.get("rows", [])

            pdf.setFont("Helvetica-Bold", 10)
            pdf.drawString(40, y, " | ".join(headers))
            y -= 14

            pdf.setFont("Helvetica", 10)
            for row in rows:
                if y < 40:
                    pdf.showPage()
                    y = height - 40
                    pdf.setFont("Helvetica", 10)
                pdf.drawString(40, y, " | ".join(row))
                y -= 14

        y -= 20  # space between sections

    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    return buffer
