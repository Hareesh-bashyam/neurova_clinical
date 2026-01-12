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


def _draw_wrapped_text(c: canvas.Canvas, text: str, x: float, y: float, max_width: float, font_name: str, font_size: int):
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


def render_pdf_from_report_json_v1(report_json: dict) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4, pageCompression=0)

    x0 = MARGIN_L
    x1 = PAGE_W - MARGIN_R
    max_w = x1 - x0

    y = PAGE_H - MARGIN_T

    sections = compose_sections_v1(report_json)

    # We'll render sequentially. Footer includes page placeholders; we patch per page by tracking pages.
    page_no = 1
    total_pages_placeholder = 1  # we will not precompute; keep placeholder approach
    # NOTE: simplest approach: render without computing total pages; replace {PAGE_TOTAL} with "1" for V1.
    # If you can compute pages later, do it, but do NOT block completion for that.

    for sec in sections:
        # Page break guard
        if y < MARGIN_B + 40 * mm:
            c.showPage()
            page_no += 1
            y = PAGE_H - MARGIN_T

        # Title
        if sec.title:
            # Safety title in red only when section key is SAFETY_FLAGS
            if sec.key == "SAFETY_FLAGS":
                c.setFillColor(colors.HexColor("#B42318"))
            else:
                c.setFillColor(colors.black)

            c.setFont(FONT_BOLD, 12)
            c.drawString(x0, y, sec.title)
            c.setFillColor(colors.black)
            y -= LINE_GAP

        # Header formatting: make first line org name bold
        if sec.key == "HEADER":
            # First line bold, next lines normal
            if sec.lines:
                c.setFont(FONT_BOLD, 14)
                c.drawString(x0, y, sec.lines[0])
                y -= LINE_GAP
            for ln in sec.lines[1:]:
                y = _draw_wrapped_text(c, ln, x0, y, max_w, FONT_MAIN, 10)
            # Divider
            c.setStrokeColor(colors.HexColor("#E6E8F0"))
            c.line(x0, y, x1, y)
            y -= SECTION_GAP
            continue

        # Table rendering (simple)
        if sec.table:
            headers = sec.table["headers"]
            rows = sec.table["rows"]

            # Draw header row
            c.setFont(FONT_BOLD, 10)
            col_w = max_w / len(headers)
            for i, h in enumerate(headers):
                c.drawString(x0 + i * col_w, y, h)
            y -= LINE_GAP

            c.setStrokeColor(colors.HexColor("#E6E8F0"))
            c.line(x0, y, x1, y)
            y -= LINE_GAP

            # Draw rows
            c.setFont(FONT_MAIN, 10)
            for r in rows:
                if y < MARGIN_B + 25 * mm:
                    c.showPage()
                    page_no += 1
                    y = PAGE_H - MARGIN_T
                for i, cell in enumerate(r):
                    c.drawString(x0 + i * col_w, y, str(cell))
                y -= LINE_GAP

            y -= SECTION_GAP
            continue

        # Normal lines rendering
        for ln in sec.lines:
            if ln.strip() == "":
                y -= LINE_GAP
                continue
            if y < MARGIN_B + 25 * mm:
                c.showPage()
                page_no += 1
                y = PAGE_H - MARGIN_T

            # Safety body: render normal black
            y = _draw_wrapped_text(c, ln.replace("{PAGE_NO}", str(page_no)).replace("{PAGE_TOTAL}", str(total_pages_placeholder)),
                                   x0, y, max_w, FONT_MAIN, 10)

        y -= SECTION_GAP

    c.save()
    return buf.getvalue()
