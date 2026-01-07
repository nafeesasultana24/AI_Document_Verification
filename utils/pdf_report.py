from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Table,
    TableStyle,
    Spacer
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch

def confidence_bar(label, value):
    filled = int(value / 10)
    empty = 10 - filled

    bar = "█" * filled + "░" * empty
    return [
        [label, f"{bar} {value}%"]
    ]

def generate_pdf(report, output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="TableText",
        fontSize=10,
        leading=14,
        wordWrap="CJK"
    ))

    elements = []

    # ---------- TITLE ----------
    elements.append(Paragraph(
        "<b>AI Government Document Verification Report</b>",
        styles["Title"]
    ))
    elements.append(Spacer(1, 12))

    # ---------- TABLE DATA ----------
    table_data = [[
        Paragraph("<b>Field</b>", styles["TableText"]),
        Paragraph("<b>Value</b>", styles["TableText"])
    ]]

    for key, value in report.items():

        if isinstance(value, dict):
            value = ", ".join(f"{k}: {v}" for k, v in value.items())

        if isinstance(value, list):
            value = ", ".join(value)

        value = "N/A" if value in [None, "", False] else str(value)

        table_data.append([
            Paragraph(str(key), styles["TableText"]),
            Paragraph(value, styles["TableText"])
        ])

    # ---------- AUTO WIDTH TABLE ----------
    table = Table(
        table_data,
        colWidths=[2.5 * inch, None],  # second column auto-expands
        repeatRows=1
    )

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),

        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),

        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    elements.append(table)

    # ---------- CONFIDENCE BARS SECTION ----------
    elements.append(Spacer(1, 16))

    elements.append(Paragraph(
        "<b>Confidence Analysis</b>",
        styles["Heading2"]
    ))

    elements.append(Spacer(1, 10))

    elements.append(Table(
        confidence_bar("OCR Confidence", report.get("OCR Confidence", 0)),
        colWidths=[2.5 * inch, None]
    ))

    elements.append(Spacer(1, 6))

    elements.append(Table(
        confidence_bar("Template Match Score", report.get("Template Match Score", 0)),
        colWidths=[2.5 * inch, None]
    ))

    elements.append(Spacer(1, 6))

    elements.append(Table(
        confidence_bar("Field Confidence", report.get("Field Confidence", 0)),
        colWidths=[2.5 * inch, None]
    ))

    elements.append(Spacer(1, 6))

    elements.append(Table(
        confidence_bar("Verification Confidence", report.get("Verification Confidence", 0)),
        colWidths=[2.5 * inch, None]
    ))


    doc.build(elements)
