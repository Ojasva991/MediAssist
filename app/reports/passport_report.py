"""
One-page, doctor-facing PDF summary of a user's Health Passport plus
their most recent symptom analyses.

Deliberately simple layout (fpdf2, no HTML-to-PDF renderer, no headless
browser) - this is a small, fast, dependency-light library with no
system-level requirements (no wkhtmltopdf/Chromium binary to install),
which matters on Render's free tier where installing a browser binary
for PDF rendering would be a real deployment risk for very little
benefit at this scale.

This is a SUMMARY handout, not a medical record and not a diagnosis -
the same "never diagnose" framing used everywhere else in this project
applies here too (see app/ai/prompts.py, app/ai/fallback.py).
"""

from datetime import datetime, timezone

from fpdf import FPDF

from app.models.history import AnalysisHistoryItem
from app.models.passport import HealthPassport

_MARGIN = 15
_LINE_HEIGHT = 6


class _ReportPDF(FPDF):
    def __init__(self, app_name: str):
        super().__init__(format="A4")
        self._app_name = app_name
        self.set_margins(_MARGIN, _MARGIN, _MARGIN)
        self.set_auto_page_break(auto=True, margin=_MARGIN)

    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 8, self._app_name, new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(110, 110, 110)
        self.cell(0, 5, "Health Summary Report - not a medical record or diagnosis", new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)
        self.ln(2)
        self.set_draw_color(200, 200, 200)
        self.line(_MARGIN, self.get_y(), 210 - _MARGIN, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(140, 140, 140)
        generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        self.cell(0, 8, f"Generated {generated} - Page {self.page_no()}", align="C")

    def section_title(self, text: str):
        self.set_font("Helvetica", "B", 11)
        self.set_fill_color(240, 244, 242)
        self.cell(0, 7, f"  {text}", new_x="LMARGIN", new_y="NEXT", fill=True)
        self.ln(1)

    def field_row(self, label: str, value: str):
        self.set_font("Helvetica", "B", 9)
        self.cell(45, _LINE_HEIGHT, label)
        self.set_font("Helvetica", "", 9)
        self.multi_cell(0, _LINE_HEIGHT, value or "Not recorded")
        # multi_cell leaves the cursor at the RIGHT margin, not back at
        # the left one - without this, the next field_row's label cell
        # would start from there and run off the page width.
        self.set_x(_MARGIN)

    def body_text(self, text: str):
        self.set_font("Helvetica", "", 9)
        self.multi_cell(0, _LINE_HEIGHT, text or "Not recorded")
        self.ln(1)


def generate_passport_report_pdf(
    passport: HealthPassport,
    history: list[AnalysisHistoryItem],
    app_name: str,
) -> bytes:
    """
    Build a one-page-ish PDF: patient info, emergency contact, medical
    profile, and up to the 5 most recent symptom analyses (if any).

    `history` is expected already-sorted most-recent-first (as returned
    by app.storage.history_store.get_history) - this function doesn't
    re-sort it, just takes the first 5.
    """
    pdf = _ReportPDF(app_name=app_name)
    pdf.add_page()

    pdf.section_title("Patient Information")
    pdf.field_row("Name:", passport.name)
    pdf.field_row("Age / Gender:", f"{passport.age} / {passport.gender}")
    pdf.field_row("Blood Group:", passport.blood_group.value)
    pdf.ln(2)

    pdf.section_title("Emergency Contact")
    pdf.field_row("Name:", passport.emergency_contact_name)
    pdf.field_row("Phone:", passport.emergency_contact_phone)
    pdf.ln(2)

    pdf.section_title("Medical Profile")
    pdf.field_row("Allergies:", passport.allergies)
    pdf.field_row("Chronic Conditions:", passport.chronic_diseases)
    pdf.field_row("Current Medications:", passport.medications)
    pdf.ln(2)

    pdf.section_title("Recent Symptom Analyses (AI-assisted, informational only)")
    recent = history[:5]
    if not recent:
        pdf.body_text("No symptom analyses on file.")
    else:
        for entry in recent:
            when = entry.created_at.strftime("%Y-%m-%d %H:%M")
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(0, _LINE_HEIGHT, f"{when} - Severity: {entry.severity.value}", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 9)
            pdf.multi_cell(0, _LINE_HEIGHT, f"Reported: {entry.symptoms} (duration: {entry.duration})")
            pdf.set_x(_MARGIN)
            if entry.possible_conditions:
                pdf.multi_cell(0, _LINE_HEIGHT, f"AI-suggested possibilities: {', '.join(entry.possible_conditions)}")
                pdf.set_x(_MARGIN)
            pdf.ln(2)

    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(
        0,
        5,
        "This report is generated from self-reported symptoms and AI-assisted triage. "
        "It is not a medical diagnosis and is not a substitute for professional medical "
        "evaluation. Please review with a qualified healthcare provider.",
    )

    return bytes(pdf.output())
