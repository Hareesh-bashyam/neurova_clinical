import io, hashlib, json
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_RIGHT

def _hash_payload(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]  # short hash for footer

def generate_report_pdf_bytes_v2(report_context: dict) -> bytes:
    """
    Uses platypus for clean 'pathology report' layout.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=16*mm,
        rightMargin=16*mm,
        topMargin=14*mm,
        bottomMargin=14*mm,
        title="Psychiatric Assessment Report"
    )

    styles = getSampleStyleSheet()
    H1 = ParagraphStyle("H1", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=14, spaceAfter=6)
    H2 = ParagraphStyle("H2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=11, spaceAfter=4)
    BODY = ParagraphStyle("BODY", parent=styles["BodyText"], fontName="Helvetica", fontSize=9, leading=12)
    SMALL = ParagraphStyle("SMALL", parent=styles["BodyText"], fontName="Helvetica", fontSize=8, leading=10)
    RIGHT = ParagraphStyle("RIGHT", parent=SMALL, alignment=TA_RIGHT)

    header = report_context.get("header", {})
    patient = report_context.get("patient", {})
    order = report_context.get("order", {})
    summary = report_context.get("summary", {})
    tests = report_context.get("tests", [])
    red_flags = report_context.get("red_flags", [])
    disclaimers = report_context.get("disclaimers", [])
    signoff = report_context.get("signoff", {})

    # Build trace hash from core parts
    trace_payload = {
        "patient": patient,
        "order": order,
        "summary": summary,
        "tests": tests,
        "red_flags": red_flags,
        "signoff": signoff,
    }
    trace_hash = _hash_payload(trace_payload)

    elements = []

    # ===== HEADER (Lab style) =====
    title = header.get("title", "Psychiatric Assessment Report")
    subtitle = header.get("subtitle", "Standardized Assessment Summary (Non-Diagnostic)")
    org_name = header.get("org_name", "NeurovaX Diagnostics")
    lab_line = header.get("lab_line", "Clinical Assessment Unit")

    elements.append(Paragraph(f"{org_name}", ParagraphStyle("ORG", parent=H1, fontSize=15)))
    elements.append(Paragraph(f"{lab_line}", ParagraphStyle("LAB", parent=BODY, fontSize=9)))
    elements.append(Spacer(1, 2*mm))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.black))
    elements.append(Spacer(1, 3*mm))
    elements.append(Paragraph(title, H1))
    elements.append(Paragraph(subtitle, BODY))
    elements.append(Spacer(1, 3*mm))

    # ===== PATIENT + ORDER INFO TABLE (2-column like pathology) =====
    info_data = [
        ["Patient Name", patient.get("full_name","-"), "Age / Sex", f"{patient.get('age','-')} / {patient.get('sex','-')}"],
        ["MRN/UHID", patient.get("mrn","-"), "Phone", patient.get("phone","-")],
        ["Battery", order.get("battery_code","-"), "Version", order.get("battery_version","-")],
        ["Administration", order.get("administration_mode","-"), "Encounter", order.get("encounter_type","-")],
        ["Created At", order.get("created_at","-"), "Completed At", order.get("completed_at","-")],
    ]
    info_table = Table(info_data, colWidths=[28*mm, 62*mm, 28*mm, 62*mm])
    info_table.setStyle(TableStyle([
        ("FONTNAME",(0,0),(-1,-1),"Helvetica"),
        ("FONTSIZE",(0,0),(-1,-1),9),
        ("BACKGROUND",(0,0),(-1,0),colors.whitesmoke),
        ("GRID",(0,0),(-1,-1),0.25,colors.grey),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("FONTNAME",(0,0),(-1,-1),"Helvetica"),
        ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
        ("FONTNAME",(2,0),(2,-1),"Helvetica-Bold"),
        ("LEFTPADDING",(0,0),(-1,-1),6),
        ("RIGHTPADDING",(0,0),(-1,-1),6),
        ("TOPPADDING",(0,0),(-1,-1),4),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 4*mm))

    # ===== SUMMARY BOX =====
    elements.append(Paragraph("Summary", H2))
    sum_data = [
        ["Primary Severity", summary.get("primary_severity","-")],
        ["Red Flags", "YES" if summary.get("has_red_flags") else "NO"]
    ]
    sum_table = Table(sum_data, colWidths=[40*mm, 140*mm])
    sum_table.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),0.25,colors.grey),
        ("BACKGROUND",(0,0),(-1,0),colors.whitesmoke),
        ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),9),
        ("LEFTPADDING",(0,0),(-1,-1),6),
        ("RIGHTPADDING",(0,0),(-1,-1),6),
        ("TOPPADDING",(0,0),(-1,-1),4),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
    ]))
    elements.append(sum_table)
    elements.append(Spacer(1, 3*mm))


    # ===== RESPONSE QUALITY FLAGS (META, NON-DIAGNOSTIC) =====
    rq = summary.get("response_quality")
    if rq:
        elements.append(Spacer(1, 2*mm))
        elements.append(Paragraph("Response Quality Flags (For Clinician Review)", H2))

        rq_rows = [
        ["Duration (sec)", str(rq.get("duration_seconds","-"))],
        ["Too Fast Flag", "YES" if rq.get("too_fast_flag") else "NO"],
        ["Straight-lining Flag", "YES" if rq.get("straight_lining_flag") else "NO"],
        ["Inconsistency Flag", "YES" if rq.get("inconsistency_flag") else "NO"],
    ]

    rq_table = Table(rq_rows, colWidths=[60*mm, 120*mm])
    rq_table.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),0.25,colors.grey),
        ("BACKGROUND",(0,0),(-1,0),colors.whitesmoke),
        ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),9),
        ("LEFTPADDING",(0,0),(-1,-1),6),
        ("TOPPADDING",(0,0),(-1,-1),4),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
    ]))

    elements.append(rq_table)
    elements.append(Spacer(1, 3*mm))


    # ===== RED FLAGS =====
    if red_flags:
        elements.append(Paragraph("Critical Flags (Clinician Attention)", H2))
        rf_rows = [[f"• {x}"] for x in red_flags[:12]]
        rf_table = Table(rf_rows, colWidths=[180*mm])
        rf_table.setStyle(TableStyle([
            ("GRID",(0,0),(-1,-1),0.25,colors.red),
            ("FONTSIZE",(0,0),(-1,-1),9),
            ("LEFTPADDING",(0,0),(-1,-1),6),
            ("TOPPADDING",(0,0),(-1,-1),4),
            ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ]))
        elements.append(rf_table)
        elements.append(Spacer(1, 3*mm))

    # ===== REMARKS (ADDED) =====
    remarks = report_context.get("remarks")
    if remarks:
        elements.append(Paragraph("Treatment Plan", H2))
        # Handle multiline remarks by splitting or just letting Paragraph handle it
        # If it's very long, Paragraph should wrap. 
        # But we might want to ensure newlines are respected if they exist.
        # ReportLab Paragraph helper: <br/> for newlines.
        formatted_remarks = remarks.replace("\n", "<br/>")
        elements.append(Paragraph(formatted_remarks, BODY))
        elements.append(Spacer(1, 3*mm))

    # ===== TEST RESULTS TABLE =====
    elements.append(Paragraph("Test Results", H2))
    table_header = ["Instrument", "Score", "Band / Interpretation"]
    rows = [table_header]
    for t in tests:
        rows.append([
            str(t.get("name","-")),
            str(t.get("score","-")),
            str(t.get("band","-")),
        ])

    res_table = Table(rows, colWidths=[70*mm, 25*mm, 85*mm], repeatRows=1)
    res_table.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),0.25,colors.grey),
        ("BACKGROUND",(0,0),(-1,0),colors.whitesmoke),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),9),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),6),
        ("RIGHTPADDING",(0,0),(-1,-1),6),
        ("TOPPADDING",(0,0),(-1,-1),4),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
    ]))
    elements.append(res_table)
    elements.append(Spacer(1, 4*mm))

    # ===== DISCLAIMER (must be near bottom, but always included) =====
    elements.append(Paragraph("Disclaimer", H2))
    d_rows = [[f"• {d}"] for d in disclaimers[:10]]
    d_table = Table(d_rows, colWidths=[180*mm])
    d_table.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),0.25,colors.grey),
        ("FONTSIZE",(0,0),(-1,-1),8.5),
        ("LEFTPADDING",(0,0),(-1,-1),6),
        ("TOPPADDING",(0,0),(-1,-1),3),
        ("BOTTOMPADDING",(0,0),(-1,-1),3),
    ]))
    elements.append(d_table)
    elements.append(Spacer(1, 4*mm))

    # ===== SIGN-OFF BOX =====
    elements.append(Paragraph("Report Validation & Clinical Responsibility", H2))
    sign_rows = [
        ["Status", signoff.get("status","PENDING"), "Signed At", signoff.get("signed_at","-")],
        ["Signed By", signoff.get("signed_by","-"), "Role", signoff.get("role","-")],
        ["Method", signoff.get("method","-"), "Reason", signoff.get("reason","-")],
    ]


    sign_table = Table(sign_rows, colWidths=[28*mm, 62*mm, 28*mm, 62*mm])
    sign_table.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),0.25,colors.grey),
        ("FONTSIZE",(0,0),(-1,-1),9),
        ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
        ("FONTNAME",(2,0),(2,-1),"Helvetica-Bold"),
        ("LEFTPADDING",(0,0),(-1,-1),6),
        ("TOPPADDING",(0,0),(-1,-1),4),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
    ]))
    elements.append(sign_table)
    elements.append(Spacer(1, 4*mm))

    # ===== FOOTER (Traceability) =====
    elements.append(HRFlowable(width="100%", thickness=0.75, color=colors.black))
    elements.append(Spacer(1, 2*mm))
    footer_left = f"Order ID: {order.get('id','-')} | Battery: {order.get('battery_code','-')} | Trace: {trace_hash}"
    footer_right = f"Generated: {order.get('completed_at','-')}"
    elements.append(Table([[Paragraph(footer_left, SMALL), Paragraph(footer_right, RIGHT)]], colWidths=[120*mm, 60*mm]))

    # ===== WATERMARK LOGIC =====
    # Check if order is accepted. If not, draw "DRAFT" watermark.
    # We default to "ACCEPTED" if missing to avoid breaking legacy reports, or "PENDING" to succeed safe?
    # Requirement: "draft water mark in initail stage when, the status has accepted the draft water mark should eliminated"
    # So if status != ACCEPTED -> Watermark
    
    order_status = order.get("status", "PENDING")

    def draw_watermark(canvas, doc):
        """
        Draws a large grey 'DRAFT' or 'PENDING ACCEPTANCE' across the page.
        """
        canvas.saveState()
        canvas.setFont("Helvetica-Bold", 60)
        canvas.setFillColor(colors.Color(0.9, 0.9, 0.9, alpha=0.5))  # Very light grey, semi-transparent
        canvas.translate(100*mm, 150*mm)
        canvas.rotate(45)
        canvas.drawCentredString(0, 0, "DRAFT REPORT")
        canvas.setFont("Helvetica-Bold", 30)
        canvas.drawCentredString(0, -30, "")
        canvas.restoreState()

    # Build
    if order_status != "ACCEPTED":
        # Apply watermark to all pages
        doc.build(elements, onFirstPage=draw_watermark, onLaterPages=draw_watermark)
    else:
        doc.build(elements)

    buf.seek(0)
    return buf.read()
