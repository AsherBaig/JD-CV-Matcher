"""
Generates an ATS-friendly PDF from the tailored CV text.

German ATS CV rules applied here:
- Single column layout (no tables, no text boxes — ATS parsers choke on these)
- Standard fonts only: Helvetica (Arial equivalent, built into every PDF viewer)
- Section headers in ALL CAPS with a full-width rule underneath
- Dates in MM/YYYY format
- No graphics, no photos, no icons in the text layer
- 1-2 pages max for students
- Consistent margins (2.5 cm — standard German business document)
"""

import re
from html import escape
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, KeepTogether
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER


# ── Colour palette ──────────────────────────────────────────────────────────
BLACK      = HexColor("#0f1117")
DARK_GREY  = HexColor("#374151")
MID_GREY   = HexColor("#6b7280")
RULE_COLOR = HexColor("#d1d5db")
ACCENT     = HexColor("#4f46e5")   # used only for the name line


# Defines all paragraph styles used in the PDF.
# Think of these as CSS classes — each style controls font, size, spacing, colour.
def build_styles() -> dict:
    return {
        "name": ParagraphStyle(
            "name", fontName="Helvetica-Bold", fontSize=20,
            textColor=ACCENT, leading=24, spaceAfter=2, alignment=TA_CENTER,
        ),
        "tagline": ParagraphStyle(
            "tagline", fontName="Helvetica", fontSize=9, leading=13,
            textColor=MID_GREY, spaceAfter=2, alignment=TA_CENTER,
        ),
        "contact": ParagraphStyle(
            "contact", fontName="Helvetica", fontSize=8.5, leading=12,
            textColor=DARK_GREY, spaceAfter=10, alignment=TA_CENTER,
        ),
        "section_header": ParagraphStyle(
            "section_header", fontName="Helvetica-Bold", fontSize=9, leading=13,
            textColor=DARK_GREY, spaceBefore=10, spaceAfter=3, letterSpacing=1.2,
        ),
        "body": ParagraphStyle(
            "body", fontName="Helvetica", fontSize=9.5, leading=14,
            textColor=BLACK, spaceAfter=3, leftIndent=0,
        ),
        "bullet": ParagraphStyle(
            "bullet", fontName="Helvetica", fontSize=9.5, leading=14,
            textColor=BLACK, spaceAfter=2, leftIndent=12,
            bulletIndent=0, bulletText="•",
        ),
        "job_title": ParagraphStyle(
            "job_title", fontName="Helvetica-Bold", fontSize=9.5, leading=14,
            textColor=BLACK, spaceAfter=1,
        ),
        "date_line": ParagraphStyle(
            "date_line", fontName="Helvetica", fontSize=8.5, leading=12,
            textColor=MID_GREY, spaceAfter=3,
        ),
    }


# Detects whether a line of text is a section header.
# Section headers are ALL CAPS lines that name a CV section.
# This is how we split the flat CV text into structured sections.
KNOWN_HEADERS = {
    "PROFESSIONAL SUMMARY", "SUMMARY", "EDUCATION", "TECHNICAL SKILLS",
    "SKILLS", "PROFESSIONAL EXPERIENCE", "EXPERIENCE", "PROJECTS",
    "CURRENTLY LEARNING", "CERTIFICATIONS", "LANGUAGES", "AVAILABILITY",
    "DEVOPS & TOOLS", "DEVOPS LAYER", "AWARDS", "VOLUNTEER",
}

def is_section_header(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    # All-caps line of 3+ characters, not a bullet point
    if stripped.startswith("•") or stripped.startswith("-"):
        return False
    # Check if it matches a known header or is fully uppercase
    upper = stripped.upper()
    if upper in KNOWN_HEADERS:
        return True
    # Fallback: fully uppercase, short enough to be a header, no digits
    if stripped == upper and 3 <= len(stripped) <= 50 and not any(c.isdigit() for c in stripped):
        return True
    return False


# Detects bullet point lines (starting with • - * or tab+bullet).
def is_bullet(line: str) -> bool:
    return line.strip().startswith(("•", "-", "*", "·"))


# Cleans a bullet line down to just its text content.
def strip_bullet(line: str) -> str:
    return re.sub(r"^[\s•\-\*·]+", "", line).strip()


# Parses the flat CV text into a list of (type, content) tuples.
# Types: "name", "contact", "header", "body", "bullet", "blank"
# This is the equivalent of a lexer/tokeniser step before rendering.
def parse_cv_lines(cv_text: str) -> list[tuple[str, str]]:
    lines = cv_text.split("\n")
    tokens = []
    first_line = True
    second_line = True

    for raw in lines:
        line = raw.rstrip()

        if not line.strip():
            tokens.append(("blank", ""))
            continue

        if first_line:
            tokens.append(("name", line.strip()))
            first_line = False
            second_line = True
            continue

        if second_line and not is_section_header(line):
            tokens.append(("tagline", line.strip()))
            second_line = False
            continue

        second_line = False

        if is_section_header(line):
            tokens.append(("header", line.strip().upper()))
        elif is_bullet(line):
            tokens.append(("bullet", strip_bullet(line)))
        else:
            tokens.append(("body", line.strip()))

    return tokens


# Converts parsed CV tokens into ReportLab Flowable objects.
# Flowables are the building blocks of a ReportLab PDF —
# think of them like DOM elements that the layout engine places on the page.
def tokens_to_flowables(tokens: list[tuple[str, str]], styles: dict) -> list:
    flowables = []
    prev_type = None

    for token_type, content in tokens:
        if token_type == "blank":
            if prev_type not in ("blank", "header"):
                flowables.append(Spacer(1, 3))
            prev_type = token_type
            continue

        # escape() converts & → &amp;  < → &lt;  > → &gt;
        # ReportLab Paragraph uses XML internally — raw & or < crash it
        safe = escape(content)

        if token_type == "name":
            flowables.append(Paragraph(safe, styles["name"]))

        elif token_type == "tagline":
            flowables.append(Paragraph(safe, styles["tagline"]))

        elif token_type == "header":
            # KeepTogether ensures the section header never appears alone at the
            # bottom of a page — it always stays with at least the rule below it
            flowables.append(KeepTogether([
                Spacer(1, 6),
                Paragraph(safe, styles["section_header"]),
                HRFlowable(width="100%", thickness=0.5, color=RULE_COLOR, spaceAfter=4),
            ]))

        elif token_type == "body":
            if " – " in content or (" - " in content and not content.startswith("•")):
                flowables.append(Paragraph(safe, styles["job_title"]))
            else:
                flowables.append(Paragraph(safe, styles["body"]))

        elif token_type == "bullet":
            flowables.append(Paragraph(safe, styles["bullet"]))

        prev_type = token_type

    return flowables


# Main function — takes the tailored CV text and saves it as a PDF at the given path.
# Returns the path of the saved PDF file.
def generate_pdf(cv_text: str, output_path: str) -> str:
    styles = build_styles()
    tokens = parse_cv_lines(cv_text)
    flowables = tokens_to_flowables(tokens, styles)

    # A4 page with 2.5 cm margins — standard German business document format
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2.2 * cm,
        title="CV",
        author="",
    )

    doc.build(flowables)
    return output_path
