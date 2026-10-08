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

_PERSON = """
CANDIDATE: name, dob, father_name, mother_name, gender
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
    _HEADER.format(doc="Class 10 / Secondary / High School marksheet or certificate.")
    + _PERSON
    + """IDENTIFIERS: roll_no, registration_no, serial_no
ACADEMIC / INSTITUTION: board, school, institution_code, academic_year, passing_year, exam_name
"""
    + _ADDRESS
    + _SCHOOL_RESULT
    + """
MARKS: per subject extract total, max_marks.
Column mapping:
- Total → total
- max_marks → 100 for every subject
Ignore the Theory / TH / Written and Practical / PR / IA columns. If no total is printed for a subject, total = null (never copy a theory or practical value into total).
"""
    + _MARKS_RULES
    + _EXTRA
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
    + """IDENTIFIERS: roll_no, registration_no, serial_no
ACADEMIC / INSTITUTION: board, school, institution_code, academic_year, passing_year, exam_name
"""
    + _ADDRESS
    + _SCHOOL_RESULT
    + """
IDENTIFIER RULES:
- Extract each field only from its printed label.
- Roll No. → roll_no.
- Registration No. → registration_no. Certificate No. is NOT registration_no;
  store it in extra_details if needed.
- Serial No. → serial_no.
- Institution / school code → institution_code; preserve slashes.
- DOB → only from an explicit Date of Birth / DOB field.
- Gender → only if explicitly printed; never infer it.
- Percentage → only if explicitly printed.
- Printed notes, certificate number, division, exam type, issue date, etc.
  may go in extra_details.

MARKS:
- Board layouts differ. Read the table headers first; never assume a fixed layout.
- For every visible subject, extract:
  total, max_marks, subject_type.
- "total" = the FINAL obtained marks from the column explicitly labelled
  Total / Total Marks / Obtained Marks, or an equivalent final-obtained-marks
  column.
- "max_marks" = 100 for every subject.
- "subject_type" = only when explicitly printed; never infer it.

- If a numeric value is visible under the Total column for a subject,
  ALWAYS extract that value as "total".
- Do not set "total" to null when a numeric value is visibly present under
  the Total column.
- Paper-wise values such as "1/040 P/042" are component marks and must NOT
  be used as "total" when a separate Total column exists.

IMPORTANT:
- Never use Max Marks as total.
- Never use Theory, Practical, Internal, External, Lab, Project, or
  Paper-wise marks as total when a separate Total column exists.
- Never calculate total from component marks.
- If no Total column exists, total = null unless another column is
  explicitly identified as the final obtained mark.
- Paper-wise values such as "1/073" or "1/051 P/028" are component marks,
  not the final total. Use the separate Total column.
- A value such as "359/500" under Grand Total / Result means:
  total_marks_obtained = 359 and total_max_marks = 500.
- Include every visible subject row, including rows with "---" or no marks.
- Grades such as A1, A2, B1, B2 are not marks.

SELF-CHECK:
- Verify that total and max_marks came from their respective headers.
- total must not exceed max_marks when max_marks is printed.
- Never join values across "/" or adjacent columns.
"""
    + _MARKS_RULES
    + _EXTRA
    + _FOOTER
)

# ============================================================
# COLLEGE / UNIVERSITY
# ============================================================

_COLLEGE_PROMPT = (
    _HEADER.format(doc="College / University marksheet, semester result, grade card or transcript.")
    + _PERSON
    + """IDENTIFIERS: roll_no, registration_no, enrollment_no, serial_no
INSTITUTION: college, university, institution_code
PROGRAM: course, course_code, branch, branch_code, exam_name, semester, session, academic_year, passing_year
"""
    + _ADDRESS
    + """
RESULT: total_marks_obtained, total_max_marks, sgpa, cgpa, percentage, result

PROGRAM DETAILS:
- Extract session, academic_year and passing_year only when explicitly printed.

RESULT VALUE PRIORITY:

CGPA AND SGPA ARE DIFFERENT FIELDS. NEVER SWAP THEM.

1. CGPA:
   - Search the ENTIRE document specifically for the label "CGPA".
   - Also recognize "C.G.P.A", "Cumulative GPA", or equivalent clearly
     labelled cumulative GPA.
   - If you see "CGPA: 8.25", output:
     "cgpa": 8.25
   - The value immediately associated with the CGPA label belongs ONLY
     to "cgpa".

2. SGPA:
   - Search the ENTIRE document specifically for the label "SGPA".
   - Also recognize "S.G.P.A", "Semester GPA", or equivalent clearly
     labelled semester GPA.
   - If you see "SGPA: 8.57", output:
     "sgpa": 8.57
   - The value immediately associated with the SGPA label belongs ONLY
     to "sgpa".

3. IMPORTANT:
   - Do NOT assume the first GPA value is SGPA.
   - Do NOT assume the first GPA value is CGPA.
   - Do NOT swap CGPA and SGPA.
   - Do NOT derive one from the other.
   - Do NOT calculate either value.
   - If the document visibly contains "CGPA: 8.25", cgpa MUST be 8.25.
   - If the document visibly contains "SGPA: 8.57", sgpa MUST be 8.57.
   - If a label is not visible, leave that field omitted.

MARKS: per subject row (key = subject name) extract subject_code, internal, external, total, max_marks, grade, grade_points, credits.
Column mapping:
- Subject Code / Code → subject_code
- Internal Obtained → internal
- External Obtained → external
- Total Obtained / Total → total
- Maximum Marks / Max → max_marks
- Grade / Letter Grade → grade
- Grade Point / Grade Points → grade_points
- Credit / Credits → credits

MARKS RULES:
- Read column headers before rows; match values to the correct subject row.
- Read EVERY row, first to last; do NOT stop after 4 or 5 subjects.
- Include all subjects, including grade-only ones and Theory, Practical, Lab, Project, CA, Audit, Elective and other types.
- Never calculate total, SGPA, CGPA or percentage.
- Never move internal/external marks between subjects.
- Never put maximum marks into obtained marks.
- Preserve subject names and codes as printed; if names repeat, use a unique key without losing either row.
- Blank, "-", AB or NA marks → null.

SEMESTER HANDLING:
- "semester" (integer) = the standalone current/result semester field (e.g. "Semester : 6" → 6; "Semester : 4" → 4).
- A combined value (e.g. "Semester : 5,6" or "3,4") means semesters covered, NOT the current semester. Store it as extra_details {"Semesters covered": "5,6"}.
- If both exist, the standalone field wins: header "3,4" + detail "4" → semester=4, extra_details {"Semesters covered": "3,4"}; header "5,6" + detail "6" → semester=6, extra_details {"Semesters covered": "5,6"}.
- NEVER put "3,4", "5,6", etc. in "semester". If only a combined value is visible, semester=null and store the combined value in extra_details; do not infer the current semester.

EXTRA DETAILS:
Store other useful labelled information that fits no field above in "extra_details": {}
(e.g. Total Subjects, Total Credits, Remarks, Result Status, Previous Semester SGPA, Certification information).
Never put table rows in extra_details.
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
    "10th_marksheet": ["total", "max_marks"],
    "12th_marksheet": ["total", "max_marks", "subject_type"],
    "college_marksheet": [
        "subject_code", "internal", "external",
        "total", "max_marks", "grade", "grade_points", "credits",
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

_MARK_TEXT_COLUMNS = {"subject_code", "grade", "subject_type"}


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