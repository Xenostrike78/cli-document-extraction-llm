"""
Per-Candidate PDF Report Generator.

Builds one PDF per candidate: identity block, a field-by-field table
(value, source document, status), derived-field explanations, and a
flags/remarks section. Uses ReportLab (pure Python, no system
dependencies like Cairo/Pango).
"""

from pathlib import Path
from typing import Dict, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)

from verification.consistency_checker import FieldConsistency
from identity.resolver import IdentityResolutionResult

STATUS_COLORS = {
    "MATCH": colors.HexColor("#d5e8d4"),
    "RESOLVED_VARIANT": colors.HexColor("#dae8fc"),
    "MISSING": colors.HexColor("#fff2cc"),
    "LOW_CONFIDENCE": colors.HexColor("#ffe6cc"),
    "MISMATCH": colors.HexColor("#f8cecc"),
}


def _status_needs_attention(status: str) -> bool:
    return status in {"MISMATCH", "LOW_CONFIDENCE", "MISSING"}


def generate_candidate_report(
    candidate_id: str,
    records: Dict[str, dict],
    derived_by_doc: Dict[str, dict],
    consistency_results: List[FieldConsistency],
    identity_results: List[IdentityResolutionResult],
    output_path: str,
):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleCustom", parent=styles["Title"], fontSize=16)
    heading_style = ParagraphStyle("HeadingCustom", parent=styles["Heading2"], spaceBefore=14)
    body_style = styles["BodyText"]

    story = []
    story.append(Paragraph("NIC Document Cross-Verification Report", title_style))
    story.append(Paragraph(f"Candidate ID: <b>{candidate_id}</b>", body_style))
    story.append(Spacer(1, 0.5 * cm))

    # --- Documents processed ---
    story.append(Paragraph("Documents Processed", heading_style))
    doc_list = ", ".join(records.keys())
    story.append(Paragraph(doc_list or "None", body_style))

    # --- Field-by-field consistency table ---
    story.append(Paragraph("Field Consistency Summary", heading_style))
    doc_labels = list(records.keys())
    header = ["Field"] + doc_labels + ["Status"]
    table_data = [header]
    row_styles = []

    for i, fc in enumerate(consistency_results, start=1):
        row = [fc.field_name]
        for doc in doc_labels:
            value = fc.values_by_doc.get(doc)
            row.append("" if value in (None, "") else str(value))
        row.append(fc.status)
        table_data.append(row)
        bg = STATUS_COLORS.get(fc.status, colors.white)
        row_styles.append(("BACKGROUND", (-1, i), (-1, i), bg))

    col_widths = [3 * cm] + [3 * cm] * len(doc_labels) + [3 * cm]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#444444")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ] + row_styles))
    story.append(table)
    story.append(Spacer(1, 0.5 * cm))

    # --- Derived fields ---
    story.append(Paragraph("Derived Fields", heading_style))
    for doc, derived in derived_by_doc.items():
        if not derived:
            continue
        story.append(Paragraph(f"<b>{doc}</b>", body_style))
        for field_name, info in derived.items():
            story.append(Paragraph(
                f"&nbsp;&nbsp;{field_name}: {info['value']} &mdash; {info['explanation']}", body_style
            ))

    # --- Identity resolution detail ---
    story.append(Paragraph("Identity Resolution Detail", heading_style))
    if not identity_results:
        story.append(Paragraph("Only one document available -- no cross-document identity comparison performed.", body_style))
    for r in identity_results:
        line = (
            f"{r.doc_a} vs {r.doc_b}: name score {r.name_score} ({r.name_decision}), "
            f"DOB match: {r.dob_match}, roll match: {r.roll_match} "
            f"&rarr; <b>{r.final_decision}</b> (confidence {r.confidence})"
        )
        story.append(Paragraph(line, body_style))
        if r.reasons:
            story.append(Paragraph("Reasons: " + "; ".join(r.reasons), body_style))

    # --- Final remarks ---
    story.append(Paragraph("Final Remarks", heading_style))
    flagged = [fc for fc in consistency_results if _status_needs_attention(fc.status)]
    if flagged:
        story.append(Paragraph(
            f"{len(flagged)} field(s) require review: " +
            ", ".join(f"{fc.field_name} ({fc.status})" for fc in flagged),
            body_style
        ))
    else:
        story.append(Paragraph("All tracked fields are consistent across documents.", body_style))

    doc = SimpleDocTemplate(str(output_path), pagesize=A4,
                             leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                             topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    doc.build(story)
    return output_path
