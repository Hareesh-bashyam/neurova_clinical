from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import black, grey, red
from reportlab.pdfgen import canvas

PAGE_WIDTH, PAGE_HEIGHT = A4
LEFT_MARGIN = 50
RIGHT_MARGIN = 50
TOP_MARGIN = PAGE_HEIGHT - 50
LINE_HEIGHT = 14


def render_report_pdf(buffer, report_json):
    c = canvas.Canvas(buffer, pagesize=A4)
    y = TOP_MARGIN

    y = render_header(c, report_json, y)
    y = render_patient_and_encounter(c, report_json, y)
    y = render_assessment_summary(c, report_json, y)
    y = render_individual_tests(c, report_json, y)
    y = render_safety_flags(c, report_json, y)
    y = render_clinical_notes(c, y)
    y = render_signoff(c, report_json, y)
    y = render_legal_disclaimer(c, y)
    render_footer(c, report_json)

    c.showPage()
    c.save()


# ============================================================
# SECTION 1 — HEADER
# ============================================================

def render_header(c, data, y):
    org = data["organization"]

    c.setFont("Helvetica-Bold", 11)
    c.drawString(LEFT_MARGIN, y, org["name"])

    c.setFont("Helvetica", 9)
    y -= LINE_HEIGHT
    c.drawString(LEFT_MARGIN, y, org["address"])

    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(
        PAGE_WIDTH - RIGHT_MARGIN,
        TOP_MARGIN,
        "Psychiatric Assessment Report",
    )

    y -= 2 * LINE_HEIGHT
    c.setFont("Helvetica", 9)
    c.drawString(LEFT_MARGIN, y, f"Report ID: {data['report_id']}")
    y -= LINE_HEIGHT
    c.drawString(
        LEFT_MARGIN,
        y,
        f"Report Date & Time: {data['audit']['created_at']}",
    )

    return y - LINE_HEIGHT


# ============================================================
# SECTION 2 — PATIENT & ENCOUNTER DETAILS
# ============================================================

def render_patient_and_encounter(c, data, y):
    patient = data["patient"]
    encounter = data["encounter"]

    c.setFont("Helvetica-Bold", 10)
    c.drawString(LEFT_MARGIN, y, "Patient & Encounter Details")
    y -= LINE_HEIGHT

    c.setFont("Helvetica", 9)
    rows = [
        f"Patient Name: {patient['name']}",
        f"Age / Gender: {patient['age']} / {patient['gender']}",
        f"Patient ID: {patient.get('patient_id', '-')}",
        f"Encounter Type: {encounter['type']}",
        f"Battery: {data['battery_code']} v{data['battery_version']}",
        f"Mode of Administration: {encounter['administration_mode']}",
        f"Assessment Date & Time: {encounter['date_time']}",
    ]

    for row in rows:
        c.drawString(LEFT_MARGIN, y, row)
        y -= LINE_HEIGHT

    return y - LINE_HEIGHT


# ============================================================
# SECTION 3 — ASSESSMENT SUMMARY
# ============================================================

def render_assessment_summary(c, data, y):
    c.setFont("Helvetica-Bold", 10)
    c.drawString(LEFT_MARGIN, y, "Assessment Summary")
    y -= LINE_HEIGHT

    c.setFont("Helvetica-Bold", 9)
    c.drawString(LEFT_MARGIN, y, "Test")
    c.drawString(200, y, "Score")
    c.drawString(260, y, "Severity")
    y -= LINE_HEIGHT

    for test in data["tests"]:
        c.setFillColor(red if test["red_flags"] else black)
        c.setFont("Helvetica", 9)
        c.drawString(LEFT_MARGIN, y, test["test_code"])
        c.drawString(200, y, str(test["score"]))
        c.drawString(260, y, test["severity"])
        y -= LINE_HEIGHT

    c.setFillColor(black)
    return y - LINE_HEIGHT


# ============================================================
# SECTION 4 — INDIVIDUAL TEST RESULTS
# ============================================================

def render_individual_tests(c, data, y):
    for test in data["tests"]:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(LEFT_MARGIN, y, test["test_code"])
        y -= LINE_HEIGHT

        c.setFont("Helvetica", 8)
        c.setFillColor(grey)
        c.drawString(LEFT_MARGIN, y, f"Test Version: {test['test_version']}")
        y -= LINE_HEIGHT

        c.setFillColor(black)
        c.setFont("Helvetica", 9)
        c.drawString(LEFT_MARGIN, y, f"Total Score: {test['score']}")
        y -= LINE_HEIGHT
        c.drawString(LEFT_MARGIN, y, f"Severity / Risk Category: {test['severity']}")
        y -= LINE_HEIGHT
        c.drawString(LEFT_MARGIN, y, f"Reference Range: {test['score_range']}")
        y -= LINE_HEIGHT

        c.drawString(
            LEFT_MARGIN,
            y,
            "Scores in this range are associated with increased symptom burden "
            "and may warrant clinical evaluation.",
        )
        y -= 2 * LINE_HEIGHT

    return y


# ============================================================
# SECTION 5 — SAFETY & RISK FLAGS (ONLY IF PRESENT)
# ============================================================

def render_safety_flags(c, data, y):
    if not data["system_notes"]["red_flag_present"]:
        return y

    c.setFillColor(red)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(LEFT_MARGIN, y, "Important Safety Information")
    y -= LINE_HEIGHT

    c.setFont("Helvetica", 9)
    for test in data["tests"]:
        for flag in test["red_flags"]:
            c.drawString(LEFT_MARGIN, y, f"- {flag}")
            y -= LINE_HEIGHT

    y -= LINE_HEIGHT
    c.drawString(LEFT_MARGIN, y, "Immediate clinical evaluation is required.")
    y -= LINE_HEIGHT
    c.drawString(LEFT_MARGIN, y, "Tele-MANAS Mental Health Helpline: 14416")

    c.setFillColor(black)
    return y - LINE_HEIGHT


# ============================================================
# SECTION 6 — CLINICAL INTERPRETATION NOTES (STATIC)
# ============================================================

def render_clinical_notes(c, y):
    c.setFont("Helvetica", 9)
    c.drawString(
        LEFT_MARGIN,
        y,
        "This report presents standardized psychometric assessment results based on "
        "patient-reported responses. The findings should be interpreted in conjunction "
        "with a comprehensive clinical evaluation.",
    )
    return y - 2 * LINE_HEIGHT


# ============================================================
# SECTION 7 — CLINICAL RESPONSIBILITY & SIGN-OFF
# ============================================================

def render_signoff(c, data, y):
    signoff = data["clinical_signoff"]

    c.setFont("Helvetica-Bold", 10)
    c.drawString(LEFT_MARGIN, y, "Clinical Responsibility & Sign-off")
    y -= LINE_HEIGHT

    c.setFont("Helvetica", 9)

    if signoff["status"] == "SIGNED":
        reviewer = signoff["reviewed_by"]
        c.drawString(LEFT_MARGIN, y, f"Reviewed by: {reviewer['name']}")
        y -= LINE_HEIGHT
        c.drawString(LEFT_MARGIN, y, f"Role: {reviewer['role']}")
        y -= LINE_HEIGHT
        if reviewer.get("registration_number"):
            c.drawString(
                LEFT_MARGIN,
                y,
                f"Registration Number: {reviewer['registration_number']}",
            )
            y -= LINE_HEIGHT
        c.drawString(LEFT_MARGIN, y, f"Reviewed At: {signoff['reviewed_at']}")
    else:
        c.drawString(
            LEFT_MARGIN,
            y,
            "This report has been system-validated and has not undergone individual "
            "clinical review.",
        )

    return y - 2 * LINE_HEIGHT


# ============================================================
# SECTION 8 — LEGAL DISCLAIMER (STATIC)
# ============================================================

def render_legal_disclaimer(c, y):
    c.setFont("Helvetica", 8)
    c.drawString(
        LEFT_MARGIN,
        y,
        "This report is generated by a software-based psychiatric assessment system and "
        "does not constitute a medical diagnosis, treatment recommendation, or "
        "prescription. Final clinical decisions must be made by a registered medical "
        "practitioner.",
    )
    return y - 2 * LINE_HEIGHT


# ============================================================
# SECTION 9 — FOOTER
# ============================================================

def render_footer(c, data):
    c.setFont("Helvetica", 8)
    footer_y = 30

    c.drawString(
        LEFT_MARGIN,
        footer_y,
        f"Report ID: {data['report_id']}",
    )

    c.drawRightString(
        PAGE_WIDTH - RIGHT_MARGIN,
        footer_y,
        f"{data['battery_code']} v{data['battery_version']} | "
        "Generated by NeurovaX Clinical Engine",
    )
