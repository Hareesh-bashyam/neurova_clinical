# reports/pdf.py
# FINAL — CANONICAL, DETERMINISTIC, SPEC-COMPLIANT PDF RENDERER
# Uses ONLY report_json as single source of truth
# ReportLab only. No Django imports. No DB access.

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black, darkgrey, red
from reportlab.lib.units import mm


def generate_report_pdf(buffer, report_json):
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    def draw_text(x, y, text, size=10, color=black, bold=False):
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.setFillColor(color)
        c.drawString(x, y, text)

    y = height - 25 * mm

    # =========================================================
    # SECTION 1 — HEADER
    # =========================================================
    draw_text(20 * mm, y, report_json["organization"]["name"], 11, bold=True)
    y -= 5 * mm
    draw_text(20 * mm, y, report_json["organization"]["address"], 8, darkgrey)

    draw_text(
        width - 90 * mm,
        height - 25 * mm,
        "Psychiatric Assessment Report",
        12,
        bold=True,
    )

    y -= 10 * mm
    draw_text(20 * mm, y, f"Report ID: {report_json['report_id']}", 9)
    y -= 5 * mm
    draw_text(20 * mm, y, f"Report Date: {report_json['audit']['created_at']}", 9)

    # =========================================================
    # SECTION 2 — PATIENT & ENCOUNTER DETAILS
    # =========================================================
    y -= 10 * mm
    c.rect(20 * mm, y - 45 * mm, width - 40 * mm, 40 * mm)

    draw_text(25 * mm, y - 10 * mm, f"Patient Name: {report_json['patient']['name']}")
    draw_text(
        25 * mm,
        y - 18 * mm,
        f"Age / Gender: {report_json['patient']['age']} / {report_json['patient']['gender']}",
    )

    pid = report_json["patient"].get("patient_id")
    if pid:
        draw_text(25 * mm, y - 26 * mm, f"Patient ID: {pid}")

    draw_text(
        width / 2,
        y - 10 * mm,
        f"Encounter Type: {report_json['encounter']['type']}",
    )
    draw_text(
        width / 2,
        y - 18 * mm,
        f"Battery: {report_json['battery_code']} (v{report_json['battery_version']})",
    )
    draw_text(
        width / 2,
        y - 26 * mm,
        f"Mode: {report_json['encounter']['administration_mode']}",
    )
    draw_text(
        width / 2,
        y - 34 * mm,
        f"Assessment Time: {report_json['encounter']['date_time']}",
    )

    y -= 55 * mm

    # =========================================================
    # SECTION 3 — ASSESSMENT SUMMARY
    # =========================================================
    draw_text(20 * mm, y, "Assessment Summary", 11, bold=True)
    y -= 8 * mm

    draw_text(20 * mm, y, "Test", bold=True)
    draw_text(80 * mm, y, "Score", bold=True)
    draw_text(120 * mm, y, "Severity", bold=True)
    y -= 5 * mm

    for t in report_json["tests"]:
        color = red if t["red_flags"] else black
        draw_text(20 * mm, y, t["test_code"], color=color)
        draw_text(80 * mm, y, str(t["score"]), color=color)
        draw_text(120 * mm, y, t["severity"], color=color)
        y -= 5 * mm

    # =========================================================
    # SECTION 4 — INDIVIDUAL TEST RESULTS
    # =========================================================
    y -= 5 * mm
    for t in report_json["tests"]:
        draw_text(20 * mm, y, t["test_code"], 11, bold=True)
        y -= 5 * mm
        draw_text(20 * mm, y, f"Test Code: {t['test_code']}", 8, darkgrey)
        y -= 5 * mm

        draw_text(25 * mm, y, f"Total Score: {t['score']}")
        y -= 4 * mm
        draw_text(25 * mm, y, f"Severity: {t['severity']}")
        y -= 4 * mm
        draw_text(25 * mm, y, f"Reference Range: {t['score_range']}")
        y -= 6 * mm

        draw_text(
            25 * mm,
            y,
            "Scores in this range are associated with increased symptom burden and may warrant clinical evaluation.",
        )
        y -= 10 * mm

    # =========================================================
    # SECTION 5 — SAFETY & RISK FLAGS
    # =========================================================
    if report_json["system_notes"]["red_flag_present"]:
        draw_text(20 * mm, y, "Important Safety Information", 11, red, bold=True)
        y -= 6 * mm
        draw_text(
            25 * mm,
            y,
            "The patient has reported thoughts of self-harm on one or more days.",
            color=red,
        )
        y -= 4 * mm
        draw_text(25 * mm, y, "Immediate clinical evaluation is required.", color=red)
        y -= 4 * mm
        draw_text(25 * mm, y, "Tele-MANAS Mental Health Helpline: 14416", color=red)
        y -= 10 * mm

    # =========================================================
    # SECTION 6 — CLINICAL INTERPRETATION NOTES
    # =========================================================
    draw_text(20 * mm, y, "Clinical Interpretation Notes", 11, bold=True)
    y -= 6 * mm
    draw_text(
        25 * mm,
        y,
        "This report presents standardized psychometric assessment results based on patient-reported responses. "
        "The findings should be interpreted in conjunction with a comprehensive clinical evaluation.",
    )
    y -= 10 * mm

    # =========================================================
    # SECTION 7 — CLINICAL RESPONSIBILITY & SIGN-OFF
    # =========================================================
    draw_text(20 * mm, y, "Clinical Responsibility & Sign-Off", 11, bold=True)
    y -= 6 * mm

    signoff = report_json["clinical_signoff"]
    if signoff["status"] == "SIGNED":
        rb = signoff["reviewed_by"]
        draw_text(25 * mm, y, f"Reviewed by: {rb['name']}")
        y -= 4 * mm
        draw_text(25 * mm, y, f"Role: {rb['role']}")
        y -= 4 * mm
        if rb.get("registration_number"):
            draw_text(
                25 * mm,
                y,
                f"Registration No: {rb['registration_number']}",
            )
            y -= 4 * mm
        draw_text(25 * mm, y, f"Reviewed at: {signoff['reviewed_at']}")
        y -= 6 * mm
        draw_text(25 * mm, y, "[ Digital Signature ]", darkgrey)
    else:
        draw_text(
            25 * mm,
            y,
            "This report has been system-validated and has not undergone individual clinical review.",
        )
    y -= 10 * mm

    # =========================================================
    # SECTION 8 — LEGAL DISCLAIMER
    # =========================================================
    draw_text(20 * mm, y, "Legal Disclaimer", 11, bold=True)
    y -= 6 * mm
    draw_text(
        25 * mm,
        y,
        "This report is generated by a software-based mental health screening system and does not constitute a clinical interpretation "
        "or treatment recommendation. Final clinical decisions must be made by a registered medical practitioner.",
    )

    # =========================================================
    # SECTION 9 — FOOTER
    # =========================================================
    c.setFont("Helvetica", 8)
    c.setFillColor(darkgrey)
    c.drawString(
        20 * mm,
        15 * mm,
        f"Report ID: {report_json['report_id']} | "
        f"{report_json['battery_code']} v{report_json['battery_version']} | "
        f"Generated by NeurovaX Clinical Engine",
    )

    c.showPage()
    c.save()
