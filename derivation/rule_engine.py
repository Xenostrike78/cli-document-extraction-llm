"""
Derived Field Computation.

Reads config/rules.json and computes target fields (e.g. annual_income,
percentage) from whichever source fields a given record actually has.

Rules are data, not code -- add a new derived field by editing the JSON,
no changes needed here.
"""

import json
import math
from pathlib import Path
from typing import Optional


RULES_PATH = (
    Path(__file__).resolve().parent.parent
    / "config"
    / "rules.json"
)


# -------------------------------------------------------------------
# RULE LOADING
# -------------------------------------------------------------------

def load_rules() -> dict:
    """Load derived-field rules from rules.json."""
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# -------------------------------------------------------------------
# GENERIC HELPERS
# -------------------------------------------------------------------

def _to_float(value):
    """
    Safely convert a value to float.

    Returns:
        float | None
    """
    if value is None or value == "":
        return None

    try:
        return float(value)
    except (ValueError, TypeError):
        return None


# -------------------------------------------------------------------
# GENERIC DERIVED FIELD HANDLER
# -------------------------------------------------------------------

def _prefer_first_present_else_multiply(
    record: dict,
    sources: list,
    multiply_by: float
):
    """
    Take the first available source field.

    If the first field is missing, use the second field and multiply
    it by multiply_by.
    """

    if not sources:
        return None, "no source fields configured"

    primary = sources[0]

    if record.get(primary) is not None:
        return (
            record[primary],
            f"taken directly from '{primary}'"
        )

    if len(sources) > 1:
        fallback = sources[1]

        if record.get(fallback) is not None:
            fallback_value = _to_float(record[fallback])

            if fallback_value is not None:
                value = round(
                    fallback_value * multiply_by,
                    2
                )

                return (
                    value,
                    f"derived: {fallback} ({record[fallback]}) "
                    f"x {multiply_by}"
                )

    return None, "no source field available"


# -------------------------------------------------------------------
# SUBJECT TOTAL CALCULATION
# -------------------------------------------------------------------

def _get_subject_total(subj: dict):
    """
    Determine the actual total marks for a subject.

    Priority:

    1. If theory + practical/internal are available,
       calculate total = theory + practical.

    2. Otherwise use explicit total_marks.

    This is important for OCR because the extracted total_marks
    can sometimes accidentally contain the theory marks instead
    of the actual total.

    Supported practical/internal keys:
        practical
        pr
        internal
        internal_assessment
        ia
    """

    theory = _to_float(subj.get("theory"))

    # Try different names that your extraction pipeline may use.
    practical = None

    practical_keys = [
        "practical",
        "pr",
        "internal",
        "internal_assessment",
        "ia",
    ]

    for key in practical_keys:
        value = _to_float(subj.get(key))

        if value is not None:
            practical = value
            break

    explicit_total = _to_float(
        subj.get("total_marks")
    )

    # ---------------------------------------------------------------
    # CASE 1:
    # Theory + practical/internal both available
    # ---------------------------------------------------------------
    if theory is not None and practical is not None:
        calculated_total = theory + practical

        return calculated_total

    # ---------------------------------------------------------------
    # CASE 2:
    # Only explicit total available
    # ---------------------------------------------------------------
    if explicit_total is not None:
        return explicit_total

    # ---------------------------------------------------------------
    # CASE 3:
    # Nothing usable
    # ---------------------------------------------------------------
    return None


# -------------------------------------------------------------------
# PERCENTAGE CALCULATION
# -------------------------------------------------------------------

def _calculate_percentage(
    record: dict,
    sources: list,
    multiply_by: float = 1.0,
    **kwargs
):
    """
    Calculate percentage from valid subject totals.

    For CBSE 12th marksheets:
        - Include recognized academic subjects.
        - Exclude co-scholastic subjects.
        - Use actual total marks.
        - Calculate the average percentage.
        - Truncate the final result to one decimal place.

    Example:

        92 + 86 + 88 + 79 + 90 + 91 = 526

        526 / 6 = 87.666...

        Truncated to one decimal = 87.6
    """

    subjects = record.get("subjects") or []

    doc_type = str(
        record.get("document_type", "")
    ).strip().lower()

    # ----------------------------------------------------------------
    # Subjects that should NOT be included in academic percentage
    # ----------------------------------------------------------------

    excluded_subjects = {
        "work experience",
        "work education",
        "general studies",
        "health and physical education",
        "health & physical education",
        "health& physical education",
        "art education",
    }

    # ----------------------------------------------------------------
    # Common CBSE Class 12 academic subjects
    # ----------------------------------------------------------------

    cbse_12th_core_subjects = {
        "english",
        "english core",

        "hindi",
        "hindi core",

        "mathematics",
        "applied mathematics",

        "physics",
        "chemistry",
        "biology",

        "computer science",
        "computer science (new)",

        "informatics practices",

        "accountancy",
        "business studies",
        "economics",
        "entrepreneurship",

        "political science",
        "history",
        "geography",
        "psychology",
        "sociology",

        "physical education",
        "home science",
        "legal studies",

        "painting",
        "sanskrit",
        "sanskrit core",

        "information technology",
    }

    valid_marks = []
    valid_subject_names = []

    # ----------------------------------------------------------------
    # Process each subject
    # ----------------------------------------------------------------

    for subj in subjects:

        if not isinstance(subj, dict):
            continue

        # Raw subject name
        name = str(
            subj.get("subject_name") or ""
        ).strip().lower()

        # Normalize multiple spaces
        name = " ".join(name.split())

        # Skip subject if name is missing
        if not name:
            continue

        # ------------------------------------------------------------
        # Exclude co-scholastic subjects
        # ------------------------------------------------------------

        if name in excluded_subjects:
            continue

        # ------------------------------------------------------------
        # For 12th marksheet, only include recognized academic
        # subjects.
        # ------------------------------------------------------------

        if doc_type == "12th_marksheet":

            if name not in cbse_12th_core_subjects:
                continue

        # ------------------------------------------------------------
        # Get actual total marks
        # ------------------------------------------------------------

        total = _get_subject_total(subj)

        if total is None:
            continue

        # ------------------------------------------------------------
        # Basic sanity check
        # ------------------------------------------------------------

        if total < 0:
            continue

        if total > 100:
            continue

        valid_marks.append(total)
        valid_subject_names.append(name)

    # ----------------------------------------------------------------
    # Calculate average
    # ----------------------------------------------------------------

    if valid_marks:

        total_marks = sum(valid_marks)
        subject_count = len(valid_marks)

        average = total_marks / subject_count

        # ------------------------------------------------------------
        # Truncate to ONE decimal place.
        #
        # Example:
        # 87.66666 -> 87.6
        #
        # This is intentional because your expected output is 87.6.
        # ------------------------------------------------------------

        percentage = (
            math.floor(average * 10) / 10
        )

        if doc_type == "12th_marksheet":

            return (
                percentage,
                (
                    f"calculated from {subject_count} valid "
                    f"CBSE 12th subjects: "
                    f"{valid_subject_names}; "
                    f"marks={valid_marks}; "
                    f"average={average:.2f}; "
                    f"truncated={percentage:.1f}"
                )
            )

        return (
            percentage,
            (
                f"calculated average of "
                f"{subject_count} subjects; "
                f"marks={valid_marks}; "
                f"average={average:.2f}; "
                f"truncated={percentage:.1f}"
            )
        )

    # ----------------------------------------------------------------
    # FALLBACK 1: Explicit percentage
    # ----------------------------------------------------------------

    explicit_percentage = _to_float(
        record.get("percentage")
    )

    if explicit_percentage is not None:

        return (
            explicit_percentage,
            "taken directly from 'percentage'"
        )

    # ----------------------------------------------------------------
    # FALLBACK 2: CGPA
    # ----------------------------------------------------------------

    cgpa = _to_float(
        record.get("cgpa")
    )

    if cgpa is not None:

        value = round(
            cgpa * 9.5,
            2
        )

        return (
            value,
            f"derived: cgpa ({record['cgpa']}) x 9.5"
        )

    # ----------------------------------------------------------------
    # Nothing available
    # ----------------------------------------------------------------

    return (
        None,
        "no subjects or explicit percentage available"
    )


# -------------------------------------------------------------------
# RULE HANDLERS
# -------------------------------------------------------------------

RULE_HANDLERS = {
    "prefer_first_present_else_multiply":
        _prefer_first_present_else_multiply,

    "calculate_percentage":
        _calculate_percentage,
}


# -------------------------------------------------------------------
# MAIN DERIVED FIELD COMPUTATION
# -------------------------------------------------------------------

def compute_derived_fields(
    record: dict,
    rules: Optional[dict] = None
) -> dict:
    """
    Compute all derived fields defined in rules.json.

    Args:
        record:
            Extracted document record.

        rules:
            Optional pre-loaded rules dictionary.

    Returns:
        {
            field_name: {
                "value": ...,
                "explanation": ...
            }
        }
    """

    rules = rules or load_rules()

    derived = {}

    for field_name, spec in rules.items():

        rule_name = spec.get("rule")

        handler = RULE_HANDLERS.get(rule_name)

        # Unknown rule
        if not handler:

            derived[field_name] = {
                "value": None,
                "explanation": (
                    f"unknown rule '{rule_name}'"
                )
            }

            continue

        # Execute rule
        try:

            value, explanation = handler(
                record,
                spec.get("sources", []),
                spec.get("multiply_by", 1)
            )

            derived[field_name] = {
                "value": value,
                "explanation": explanation
            }

        except Exception as e:

            derived[field_name] = {
                "value": None,
                "explanation": (
                    f"error while calculating "
                    f"'{field_name}': {str(e)}"
                )
            }

    return derived