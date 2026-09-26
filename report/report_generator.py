"""
Per-Candidate PDF Report Generator.

Builds one PDF per candidate containing:
- Candidate identity information
- Documents processed
- Complete document-extracted fields
- Subject-wise marks
- Field-by-field consistency
- Derived-field explanations
- Identity-resolution results
- Flags and final remarks

Uses ReportLab.
"""

from pathlib import Path
from typing import Dict, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


from verification.consistency_checker import FieldConsistency
from identity.resolver import IdentityResolutionResult


# ============================================================
# STATUS COLORS
# ============================================================

STATUS_COLORS = {
    "MATCH": colors.HexColor("#d5e8d4"),
    "RESOLVED_VARIANT": colors.HexColor("#dae8fc"),
    "MISSING": colors.HexColor("#fff2cc"),
    "LOW_CONFIDENCE": colors.HexColor("#ffe6cc"),
    "MISMATCH": colors.HexColor("#f8cecc"),
}


def _status_needs_attention(status: str) -> bool:
    return status in {
        "MISMATCH",
        "LOW_CONFIDENCE",
        "MISSING",
    }


def _display_value(value):
    """
    Convert extracted values into readable PDF text.
    """
    if value is None:
        return "—"

    if value == "":
        return "—"

    return str(value)


def _safe_paragraph(text, style):
    """
    Safely create a ReportLab Paragraph.
    """
    if text is None:
        text = "—"

    return Paragraph(str(text), style)


# ============================================================
# MAIN REPORT GENERATOR
# ============================================================

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

    # --------------------------------------------------------
    # Styles
    # --------------------------------------------------------

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleCustom",
        parent=styles["Title"],
        fontSize=16,
        leading=20,
        spaceAfter=8,
    )

    heading_style = ParagraphStyle(
        "HeadingCustom",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        spaceBefore=14,
        spaceAfter=6,
    )

    subheading_style = ParagraphStyle(
        "SubHeadingCustom",
        parent=styles["Heading3"],
        fontSize=10,
        leading=13,
        spaceBefore=8,
        spaceAfter=4,
    )

    body_style = ParagraphStyle(
        "BodyCustom",
        parent=styles["BodyText"],
        fontSize=8.5,
        leading=11,
    )

    small_style = ParagraphStyle(
        "SmallCustom",
        parent=styles["BodyText"],
        fontSize=7.5,
        leading=9,
    )

    story = []

    # ========================================================
    # TITLE
    # ========================================================

    story.append(
        Paragraph(
            "NIC Document Cross-Verification Report",
            title_style,
        )
    )

    story.append(
        Paragraph(
            f"Candidate ID: <b>{candidate_id}</b>",
            body_style,
        )
    )

    story.append(Spacer(1, 0.4 * cm))

    # ========================================================
    # 1. DOCUMENTS PROCESSED
    # ========================================================

    story.append(
        Paragraph(
            "1. Documents Processed",
            heading_style,
        )
    )

    if records:
        document_table_data = [
            [
                _safe_paragraph("Document", small_style),
                _safe_paragraph("Status", small_style),
            ]
        ]

        for doc_name in records.keys():
            document_table_data.append(
                [
                    _safe_paragraph(doc_name, small_style),
                    _safe_paragraph("Processed", small_style),
                ]
            )

        document_table = Table(
            document_table_data,
            colWidths=[12 * cm, 4 * cm],
            repeatRows=1,
        )

        document_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#444444"),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                ]
            )
        )

        story.append(document_table)

    else:
        story.append(
            Paragraph(
                "No documents were processed.",
                body_style,
            )
        )

    # ========================================================
    # 2. COMPLETE DOCUMENT EXTRACTION
    # ========================================================

    story.append(
        Paragraph(
            "2. Extracted Document Information",
            heading_style,
        )
    )

    """
    Fields added to your DocumentExtraction schema:

    document_type
    name
    dob
    father_name
    mother_name
    guardian_name
    roll_no
    registration_no
    school
    document_date
    percentage
    cgpa
    result
    subjects
    """

    personal_fields = [
        ("Name", "name"),
        ("Date of Birth", "dob"),
        ("Father's Name", "father_name"),
        ("Mother's Name", "mother_name"),
        ("Guardian Name", "guardian_name"),
        ("Roll Number", "roll_no"),
        ("Registration Number", "registration_no"),
        ("School", "school"),
        ("Document Date", "document_date"),
        ("Percentage", "percentage"),
        ("CGPA", "cgpa"),
        ("Result", "result"),
    ]

    for doc_name, record in records.items():

        story.append(
            Paragraph(
                f"<b>{doc_name}</b>",
                subheading_style,
            )
        )

        # ----------------------------------------------------
        # Basic document information
        # ----------------------------------------------------

        document_type = record.get("document_type")

        if document_type:
            story.append(
                Paragraph(
                    f"Document Type: <b>{_display_value(document_type)}</b>",
                    body_style,
                )
            )

        field_table_data = [
            [
                _safe_paragraph("Field", small_style),
                _safe_paragraph("Extracted Value", small_style),
            ]
        ]

        for label, key in personal_fields:

            value = record.get(key)

            field_table_data.append(
                [
                    _safe_paragraph(label, small_style),
                    _safe_paragraph(
                        _display_value(value),
                        small_style,
                    ),
                ]
            )

        field_table = Table(
            field_table_data,
            colWidths=[5 * cm, 11 * cm],
            repeatRows=1,
        )

        field_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#444444"),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                ]
            )
        )

        story.append(field_table)

        # ====================================================
        # 3. SUBJECT-WISE MARKS
        # ====================================================

        story.append(
            Paragraph(
                "Subject-wise Marks",
                subheading_style,
            )
        )

        subjects = record.get("subjects", [])

        if subjects:

            marks_table_data = [
                [
                    _safe_paragraph("Subject", small_style),
                    _safe_paragraph("Code", small_style),
                    _safe_paragraph("Theory", small_style),
                    _safe_paragraph("Practical", small_style),
                    _safe_paragraph("Total", small_style),
                ]
            ]

            for subject in subjects:

                # Supports both dictionaries and Pydantic-style objects
                if hasattr(subject, "model_dump"):
                    subject = subject.model_dump()

                subject_name = subject.get("subject_name")
                subject_code = subject.get("subject_code")
                theory = subject.get("theory_marks")
                practical = subject.get("practical_marks")
                total = subject.get("total_marks")

                marks_table_data.append(
                    [
                        _safe_paragraph(
                            _display_value(subject_name),
                            small_style,
                        ),
                        _safe_paragraph(
                            _display_value(subject_code),
                            small_style,
                        ),
                        _safe_paragraph(
                            _display_value(theory),
                            small_style,
                        ),
                        _safe_paragraph(
                            _display_value(practical),
                            small_style,
                        ),
                        _safe_paragraph(
                            _display_value(total),
                            small_style,
                        ),
                    ]
                )

            marks_table = Table(
                marks_table_data,
                colWidths=[
                    6 * cm,
                    2 * cm,
                    2.2 * cm,
                    2.2 * cm,
                    2.2 * cm,
                ],
                repeatRows=1,
            )

            marks_table.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, 0),
                            colors.HexColor("#444444"),
                        ),
                        (
                            "TEXTCOLOR",
                            (0, 0),
                            (-1, 0),
                            colors.white,
                        ),
                        (
                            "GRID",
                            (0, 0),
                            (-1, -1),
                            0.5,
                            colors.grey,
                        ),
                        (
                            "VALIGN",
                            (0, 0),
                            (-1, -1),
                            "MIDDLE",
                        ),
                        (
                            "FONTSIZE",
                            (0, 0),
                            (-1, -1),
                            7.5,
                        ),
                    ]
                )
            )

            story.append(marks_table)

        else:

            story.append(
                Paragraph(
                    "No subject-wise marks extracted.",
                    body_style,
                )
            )

        story.append(Spacer(1, 0.3 * cm))

    # ========================================================
    # 4. FIELD-BY-FIELD CONSISTENCY
    # ========================================================

    story.append(
        Paragraph(
            "3. Field Consistency Summary",
            heading_style,
        )
    )

    doc_labels = list(records.keys())

    if consistency_results:

        header = (
            ["Field"]
            + doc_labels
            + ["Status"]
        )

        table_data = [header]
        row_styles = []

        for i, fc in enumerate(
            consistency_results,
            start=1,
        ):

            row = [
                fc.field_name
            ]

            for doc in doc_labels:

                value = fc.values_by_doc.get(doc)

                row.append(
                    _display_value(value)
                )

            row.append(fc.status)

            table_data.append(row)

            bg = STATUS_COLORS.get(
                fc.status,
                colors.white,
            )

            row_styles.append(
                (
                    "BACKGROUND",
                    (-1, i),
                    (-1, i),
                    bg,
                )
            )

        # Dynamically calculate widths
        field_width = 3.2 * cm
        status_width = 3 * cm

        available_width = (
            17 * cm
            - field_width
            - status_width
        )

        doc_width = (
            available_width / len(doc_labels)
            if doc_labels
            else 4 * cm
        )

        col_widths = (
            [field_width]
            + [doc_width] * len(doc_labels)
            + [status_width]
        )

        consistency_table = Table(
            table_data,
            colWidths=col_widths,
            repeatRows=1,
        )

        consistency_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#444444"),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                ]
                + row_styles
            )
        )

        story.append(consistency_table)

    else:

        story.append(
            Paragraph(
                "No consistency results available.",
                body_style,
            )
        )

    # ========================================================
    # 5. DERIVED FIELDS
    # ========================================================

    story.append(
        Paragraph(
            "4. Derived Fields",
            heading_style,
        )
    )

    has_derived = False

    for doc, derived in derived_by_doc.items():

        if not derived:
            continue

        has_derived = True

        story.append(
            Paragraph(
                f"<b>{doc}</b>",
                subheading_style,
            )
        )

        derived_table_data = [
            [
                _safe_paragraph("Field", small_style),
                _safe_paragraph("Value", small_style),
                _safe_paragraph("Explanation", small_style),
            ]
        ]

        for field_name, info in derived.items():

            value = info.get("value")
            explanation = info.get(
                "explanation",
                "",
            )

            derived_table_data.append(
                [
                    _safe_paragraph(
                        field_name,
                        small_style,
                    ),
                    _safe_paragraph(
                        _display_value(value),
                        small_style,
                    ),
                    _safe_paragraph(
                        explanation,
                        small_style,
                    ),
                ]
            )

        derived_table = Table(
            derived_table_data,
            colWidths=[
                4 * cm,
                3 * cm,
                10 * cm,
            ],
            repeatRows=1,
        )

        derived_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#444444"),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                ]
            )
        )

        story.append(derived_table)

    if not has_derived:

        story.append(
            Paragraph(
                "No derived fields were generated.",
                body_style,
            )
        )

    # ========================================================
    # 6. IDENTITY RESOLUTION
    # ========================================================

    story.append(
        Paragraph(
            "5. Identity Resolution Detail",
            heading_style,
        )
    )

    if not identity_results:

        story.append(
            Paragraph(
                "Only one document available — no cross-document "
                "identity comparison performed.",
                body_style,
            )
        )

    else:

        identity_table_data = [
            [
                _safe_paragraph("Documents", small_style),
                _safe_paragraph("Name Score", small_style),
                _safe_paragraph("Name Decision", small_style),
                _safe_paragraph("DOB Match", small_style),
                _safe_paragraph("Roll Match", small_style),
                _safe_paragraph("Final Decision", small_style),
                _safe_paragraph("Confidence", small_style),
            ]
        ]

        for r in identity_results:

            identity_table_data.append(
                [
                    _safe_paragraph(
                        f"{r.doc_a} vs {r.doc_b}",
                        small_style,
                    ),
                    _safe_paragraph(
                        _display_value(r.name_score),
                        small_style,
                    ),
                    _safe_paragraph(
                        _display_value(r.name_decision),
                        small_style,
                    ),
                    _safe_paragraph(
                        _display_value(r.dob_match),
                        small_style,
                    ),
                    _safe_paragraph(
                        _display_value(r.roll_match),
                        small_style,
                    ),
                    _safe_paragraph(
                        _display_value(r.final_decision),
                        small_style,
                    ),
                    _safe_paragraph(
                        _display_value(r.confidence),
                        small_style,
                    ),
                ]
            )

        identity_table = Table(
            identity_table_data,
            colWidths=[
                3.5 * cm,
                2 * cm,
                2.5 * cm,
                2 * cm,
                2 * cm,
                2.5 * cm,
                2 * cm,
            ],
            repeatRows=1,
        )

        identity_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#444444"),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                ]
            )
        )

        story.append(identity_table)

        # Reasons
        for r in identity_results:

            if r.reasons:

                story.append(
                    Paragraph(
                        f"<b>{r.doc_a} vs {r.doc_b} — Reasons:</b> "
                        + "; ".join(r.reasons),
                        small_style,
                    )
                )

    # ========================================================
    # 7. FLAGS / REMARKS
    # ========================================================

    story.append(
        Paragraph(
            "6. Flags and Remarks",
            heading_style,
        )
    )

    flagged = [
        fc
        for fc in consistency_results
        if _status_needs_attention(fc.status)
    ]

    if flagged:

        flags_table_data = [
            [
                _safe_paragraph("Field", small_style),
                _safe_paragraph("Status", small_style),
                _safe_paragraph("Values", small_style),
            ]
        ]

        for fc in flagged:

            values = []

            for doc in doc_labels:

                value = fc.values_by_doc.get(doc)

                values.append(
                    f"{doc}: {_display_value(value)}"
                )

            flags_table_data.append(
                [
                    _safe_paragraph(
                        fc.field_name,
                        small_style,
                    ),
                    _safe_paragraph(
                        fc.status,
                        small_style,
                    ),
                    _safe_paragraph(
                        "<br/>".join(values),
                        small_style,
                    ),
                ]
            )

        flags_table = Table(
            flags_table_data,
            colWidths=[
                4 * cm,
                3 * cm,
                10 * cm,
            ],
            repeatRows=1,
        )

        flags_style = [
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#444444"),
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white,
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey,
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP",
            ),
        ]

        for i, fc in enumerate(flagged, start=1):

            bg = STATUS_COLORS.get(
                fc.status,
                colors.white,
            )

            flags_style.append(
                (
                    "BACKGROUND",
                    (1, i),
                    (1, i),
                    bg,
                )
            )

        flags_table.setStyle(
            TableStyle(flags_style)
        )

        story.append(flags_table)

    else:

        story.append(
            Paragraph(
                "No fields require attention.",
                body_style,
            )
        )

    # ========================================================
    # 8. FINAL REMARKS
    # ========================================================

    story.append(
        Paragraph(
            "7. Final Remarks",
            heading_style,
        )
    )

    if flagged:

        story.append(
            Paragraph(
                f"<b>{len(flagged)}</b> field(s) require review: "
                + ", ".join(
                    f"{fc.field_name} ({fc.status})"
                    for fc in flagged
                ),
                body_style,
            )
        )

    else:

        story.append(
            Paragraph(
                "All tracked fields are consistent across the "
                "available documents.",
                body_style,
            )
        )

    # ========================================================
    # BUILD PDF
    # ========================================================

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    doc.build(story)

    return output_path