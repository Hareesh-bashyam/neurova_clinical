from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors

from .report_composer_v1 import compose_sections_v1


PAGE_W, PAGE_H = A4

MARGIN_L = 18 * mm
MARGIN_R = 18 * mm
MARGIN_T = 16 * mm
MARGIN_B = 16 * mm

LINE_GAP = 5.2 * mm
SECTION_GAP = 6.5 * mm

FONT_MAIN = "Helvetica"
FONT_BOLD = "Helvetica-Bold"


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def _draw_wrapped_text(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    max_width: float,
    font_name: str,
    font_size: int,
):
    c.setFont(font_name, font_size)
    words = text.split(" ")
    line = ""
    lines = []

    for w in words:
        test = (line + " " + w).strip()
        if c.stringWidth(test, font_name, font_size) <= max_width:
            line = test
        else:
            lines.append(line)
            line = w

    if line:
        lines.append(line)

    for ln in lines:
        c.drawString(x, y, ln)
        y -= LINE_GAP

    return y


def _draw_footer(c: canvas.Canvas, page_no: int):
    """
    Minimal medical-style footer.
    Right aligned page number only.
    """
    c.setFont(FONT_MAIN, 9)
    c.setFillColor(colors.grey)
    c.drawRightString(
        PAGE_W - MARGIN_R,
        MARGIN_B - 6 * mm,
        f"Page {page_no}",
    )
    c.setFillColor(colors.black)


# -------------------------------------------------
# MAIN RENDERER
# -------------------------------------------------
def render_pdf_from_report_json_v1(report_json: dict) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4, pageCompression=0)

    x0 = MARGIN_L
    x1 = PAGE_W - MARGIN_R
    max_w = x1 - x0
    y = PAGE_H - MARGIN_T

    sections = compose_sections_v1(report_json)

    page_no = 1

    for sec in sections:
        if y < MARGIN_B + 40 * mm:
            _draw_footer(c, page_no)
            c.showPage()
            page_no += 1
            y = PAGE_H - MARGIN_T

        # -------------------------
        # Section title
        # -------------------------
        if sec.title:
            if sec.key == "SAFETY_FLAGS":
                c.setFillColor(colors.HexColor("#B42318"))
            else:
                c.setFillColor(colors.black)

            c.setFont(FONT_BOLD, 12)
            c.drawString(x0, y, sec.title)
            c.setFillColor(colors.black)
            y -= LINE_GAP

        # -------------------------
        # HEADER
        # -------------------------
        if sec.key == "HEADER":
            if sec.lines:
                c.setFont(FONT_BOLD, 14)
                c.drawString(x0, y, sec.lines[0])
                y -= LINE_GAP

            for ln in sec.lines[1:]:
                y = _draw_wrapped_text(
                    c, ln, x0, y, max_w, FONT_MAIN, 10
                )

            c.setStrokeColor(colors.HexColor("#E6E8F0"))
            c.line(x0, y, x1, y)
            y -= SECTION_GAP
            continue

        # -------------------------
        # TABLE SECTIONS
        # -------------------------
        if sec.table:
            headers = sec.table["headers"]
            rows = sec.table["rows"]

            c.setFont(FONT_BOLD, 10)
            col_w = max_w / len(headers)

            for i, h in enumerate(headers):
                c.drawString(x0 + i * col_w, y, h)

            y -= LINE_GAP
            c.setStrokeColor(colors.HexColor("#E6E8F0"))
            c.line(x0, y, x1, y)
            y -= LINE_GAP

            c.setFont(FONT_MAIN, 10)
            for r in rows:
                if y < MARGIN_B + 25 * mm:
                    _draw_footer(c, page_no)
                    c.showPage()
                    page_no += 1
                    y = PAGE_H - MARGIN_T

                for i, cell in enumerate(r):
                    c.drawString(x0 + i * col_w, y, str(cell))

                y -= LINE_GAP

            y -= SECTION_GAP
            continue

        # -------------------------
        # NORMAL TEXT
        # -------------------------
        for ln in sec.lines:
            if ln.strip() == "":
                y -= LINE_GAP
                continue

            if y < MARGIN_B + 25 * mm:
                _draw_footer(c, page_no)
                c.showPage()
                page_no += 1
                y = PAGE_H - MARGIN_T

            y = _draw_wrapped_text(
                c, ln, x0, y, max_w, FONT_MAIN, 10
            )

        y -= SECTION_GAP

    # Footer on last page
    _draw_footer(c, page_no)

    c.save()
    return buf.getvalue()
