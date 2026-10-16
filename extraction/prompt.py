from config.schemas import Class10Schema, Class12Schema, CollegeSchema


# ============================================================
# SHARED FRAGMENTS
# ============================================================

_COMMON_RULES = """
GENERAL RULES:
- Read the entire document. Extract ONLY information explicitly visible.
- Never guess, infer, calculate or correct values.
- Identify fields by printed labels and table column headers.
- Missing, blank, unclear or unreadable fields, and empty/"-"/"AB"/"NA"/non-numeric marks, must be null.
- Preserve names, IDs and text as printed; keep dates in the visible format.
- Do not confuse Roll No., Registration No., Enrollment No. and Serial No.
- Ignore the filename, browser headers, URLs, timestamps and scan metadata.
- Read EVERY row of EVERY visible marks/result table, top to bottom. Do not stop early or omit any subject type (Practical, CA, Audit, Project, Lab, Elective, etc.).
- Before returning JSON, verify every visible subject row is in "marks".
- Extract printed result values (CGPA, SGPA, percentage, total marks, etc.) exactly; never replace them with calculated values.
- Do not merge information from different documents.
- Numeric fields (marks, totals, percentage, SGPA, CGPA, credits, years) must be plain numbers only: no "/", "%", commas or units.
- If a total is printed as "obtained/maximum" (e.g. 350/500), put 350 in total_marks_obtained and 500 in total_max_marks.
"""

_HEADER = "You are an academic document extraction system.\n\nDOCUMENT TYPE:\n{doc}\n\nExtract the following if explicitly printed.\n"

# _Person updated by saqib
_PERSON = """
CANDIDATE FIELDS:
- name
- father_name
- mother_name

RULES:
- Extract the candidate's name from the candidate-name field or
  the sentence identifying the person who passed the examination.
- Extract father_name and mother_name only when supported by
  explicit labels or clear parent-identifying text.
- Never confuse the candidate's name with either parent's name.
- Preserve names as printed.
- Do not extract DOB, gender, address, or other personal details.
"""

_ADDRESS = "ADDRESS: address, city, district, state, pincode\n"

_SCHOOL_RESULT = "RESULT: total_marks_obtained, total_max_marks, percentage, result\n"

_MARKS_RULES = """
MARKS RULES:
- Use the subject name as the key, preserved as printed; if names repeat, use a unique key without losing any row.
- Include every subject row shown.
- Absent column → null.
- Never calculate totals or percentages.
- Never put maximum marks into obtained marks.
"""

_EXTRA = """
EXTRA DETAILS:
Store other useful labelled information that fits no field above in "extra_details": {}.
Never put marks-table rows in extra_details.
"""

_FOOTER = "\nReturn ONLY valid JSON in the OUTPUT FORMAT given below.\n"


# ============================================================
# CLASS 10
# ============================================================

_CLASS10_PROMPT = (
    _HEADER.format(
        doc="Class 10 / Secondary / High School marksheet or certificate."
    )
    + _PERSON
    + """
INSTITUTION:
- board
- school

OVERALL RESULT:
- total_marks_obtained
- total_max_marks
- percentage
- result

SUBJECT MARKS:
For each subject, extract:
- total
- max_marks

RULES:
- Preserve the subject name as printed.
- Extract every visible subject row.
- total must represent the final obtained marks.
- max_marks must represent the maximum marks.
- Do not confuse obtained marks with maximum marks.
- Do not calculate totals or percentages.
- If a value is missing or unreadable, use null.
- Ignore roll numbers, registration numbers, serial numbers,
  institution codes, dates, addresses, and other unrequested fields.
"""
    + _MARKS_RULES
    + _FOOTER
)


# ============================================================
# CLASS 12
# ============================================================

_CLASS12_PROMPT = (
    _HEADER.format(
        doc="Class 12 / Senior Secondary / Intermediate marksheet or certificate."
    )
    + _PERSON
    + """
INSTITUTION:
- board
- school

OVERALL RESULT:
- total_marks_obtained
- total_max_marks
- percentage
- result

SUBJECT MARKS:
For every visible subject, extract:
- total
- max_marks
- subject_type

RULES:
- Read the table headers before extracting marks.
- total must represent the final obtained marks.
- max_marks must represent the maximum marks.
- subject_type must be extracted only when explicitly printed.
- Do not confuse grades with marks.
- Do not calculate totals or percentages.
- Include every visible subject, even if some marks are missing.
- Ignore roll numbers, registration numbers, serial numbers,
  institution codes, dates, addresses, and other unrequested fields.
"""
    + _MARKS_RULES
    + _FOOTER
)

# ============================================================
# COLLEGE / UNIVERSITY
# ============================================================

_COLLEGE_PROMPT = (
    _HEADER.format(
        doc="College / University marksheet, semester result, grade card or transcript."
    )
    + _PERSON
    + """
INSTITUTION:
- college
- university

PROGRAMME:
- course
- branch
- semester
- academic_year
- passing_year

OVERALL RESULT:
- total_marks_obtained
- total_max_marks
- sgpa
- cgpa
- percentage
- result

SUBJECT MARKS:
For every visible subject, extract:
- internal
- external
- total
- max_marks
- grade
- grade_points
- credits

GPA RULES:
- Extract SGPA and CGPA independently.
- Never swap SGPA and CGPA.
- Never calculate either value.
- Extract each value only when supported by the printed label.

SEMESTER RULES:
- Extract semester as an integer only when a standalone semester
  value is visible.
- If the document shows a combined value such as "5,6", do not
  place it in semester.
- Store a combined semester value in extra_details as
  "Semesters covered".
- Do not infer a semester from other fields.

EXTRA DETAILS:
- Store only "Semesters covered" and "Result Status", when printed.
- Do not store any other extra details.
- Never put subject marks in extra_details.

GENERAL RULES:
- Preserve subject names as printed.
- Read every visible subject row.
- Do not calculate marks, percentages, SGPA, or CGPA.
- Use null for missing or unreadable values.
- Ignore roll numbers, registration numbers, enrollment numbers,
  serial numbers, institution codes, course codes, branch codes,
  exam names, session details, addresses, and other unrequested fields.
"""
    + _FOOTER
)

# ============================================================
# REGISTRY AND COMPACT FORMAT
# ============================================================

_REGISTRY = {
    "10th_marksheet": (_CLASS10_PROMPT, Class10Schema),
    "12th_marksheet": (_CLASS12_PROMPT, Class12Schema),
    "college_marksheet": (_COLLEGE_PROMPT, CollegeSchema),
}

# Column order of each per-subject array in the compact "marks" output.
MARK_COLUMNS = {
    "10th_marksheet": [
        "total",
        "max_marks",
    ],
    "12th_marksheet": [
        "total",
        "max_marks",
        "subject_type",
    ],
    "college_marksheet": [
        "internal",
        "external",
        "total",
        "max_marks",
        "grade",
        "grade_points",
        "credits",
    ],
}


# True  -> keep the model output short (needed on Groq free tier, 1000 output tokens/min).
# False -> original behaviour: store every useful labelled detail in extra_details.
LEAN_OUTPUT = True


def get_schema(document_type):
    if document_type not in _REGISTRY:
        raise ValueError(f"Unsupported document type: {document_type}")
    return _REGISTRY[document_type][1]


def build_extraction_prompt(document_type, part="all"):
    if document_type not in _REGISTRY:
        raise ValueError(f"Unsupported document type: {document_type}")

    prompt, _ = _REGISTRY[document_type]
    cols = MARK_COLUMNS[document_type]

    if not LEAN_OUTPUT:
        extra_rule = '- "extra_details": an object (omit it if empty). Never put marks-table rows in it.'
    elif document_type == "college_marksheet":
        extra_rule = (
            '- "extra_details": keep it minimal (omit if empty). Only these, if printed: '
            '"Semesters covered", Total Subjects, Total Credits, Remarks, Result Status, '
            'Previous Semester SGPA, Certification information. Omit every other labelled item. '
            'Never put marks-table rows in it.'
        )
    else:
        extra_rule = (
            '- "extra_details": keep it minimal (omit if empty): only a few essential labelled items '
            'not covered by the fields above. Never put marks-table rows in it.'
        )

    minify = "Output compact single-line JSON: no indentation, no line breaks, no extra spaces."

    if part == "marks":
        output_block = f"""OUTPUT FORMAT:
Return ONLY one valid JSON object of the form {{"marks": {{"SUBJECT NAME": [v1, v2, ...]}}}} and NOTHING else.
Do NOT output any other field (no name, no result, no extra_details).
Values in each array follow exactly this order:
  {", ".join(cols)}
Use null for a missing value in the middle so positions never shift; trailing null values may be omitted. Include every subject row.
{minify}
Do not return markdown. Do not explain your answer."""
    else:
        marks_rule = (
            '- Do NOT include "marks" in this response; marks are extracted separately.'
            if part == "header" else
            f'- "marks": {{"SUBJECT NAME": [v1, v2, ...]}}. Values follow exactly this order:\n'
            f'  {", ".join(cols)}\n'
            '  Use null for a missing value in the middle so positions never shift; '
            'trailing null values may be omitted. Include every subject row.'
        )
        output_block = f"""OUTPUT FORMAT:
Return ONLY one valid JSON object.
- Put every scalar field at the TOP LEVEL of the JSON, using the exact field names above. NEVER group fields into sub-objects (no "address": {{"city": ...}}, no "result": {{...}}); the headings above are labels, not keys.
- Include ONLY scalar fields that have a printed value. OMIT any field that would be null.
- Do NOT include "document_type".
{marks_rule}
{extra_rule}
{minify}
Do not return markdown. Do not explain your answer."""

    return f"""
{prompt}

{_COMMON_RULES}

{output_block}
"""


import typing

_MARK_TEXT_COLUMNS = {"grade", "subject_type"}


def _to_number(value):
    """Parse '350', '85.2%', '1,702' -> float. Return None if not numeric."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    text = str(value).strip().replace(",", "").rstrip("%").strip()
    try:
        return float(text)
    except ValueError:
        return None


def _is_numeric_field(annotation):
    args = typing.get_args(annotation) or (annotation,)
    return any(a in (int, float) for a in args)


def _coerce_scalars(flat, schema):
    """Make numeric schema fields numeric; split 'obtained/max' totals."""
    for name, field in schema.model_fields.items():
        value = flat.get(name)
        if not isinstance(value, str) or not _is_numeric_field(field.annotation):
            continue
        if "/" in value and name in ("total_marks_obtained", "total_max_marks"):
            left, _, right = value.partition("/")
            obtained, maximum = _to_number(left), _to_number(right)
            if obtained is not None and maximum is not None:
                flat["total_marks_obtained"] = obtained
                flat["total_max_marks"] = maximum
                continue
        number = _to_number(value)
        if number is not None:
            flat[name] = number


def expand_compact(data, document_type):
    """Rebuild the full schema-shaped dict from the compact model output."""
    schema = get_schema(document_type)
    cols = MARK_COLUMNS[document_type]

    marks = {}
    for subject, row in (data.get("marks") or {}).items():
        if not isinstance(row, list) or len(row) > len(cols):
            raise ValueError(
                f"Malformed marks row for {subject!r}: expected at most {len(cols)} values, got {row!r}"
            )
        row = row + [None] * (len(cols) - len(row))
        cells = dict(zip(cols, row))
        for col, cell in cells.items():
            if col not in _MARK_TEXT_COLUMNS and cell is not None:
                cells[col] = _to_number(cell)   # "AB", "-", "NA" -> None
        marks[subject] = cells

    # Safeguard: flatten any grouped sub-objects the model may have produced.
    flat = {}
    for key, value in data.items():
        if key in ("marks", "extra_details"):
            continue
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                if sub_key in schema.model_fields and sub_value is not None:
                    flat.setdefault(sub_key, sub_value)
        else:
            flat[key] = value

    _coerce_scalars(flat, schema)

    full = {name: None for name in schema.model_fields}
    full.update(flat)
    full["marks"] = marks
    full["extra_details"] = data.get("extra_details") or {}
    full["document_type"] = document_type
    return full