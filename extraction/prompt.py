import json

from config.schemas import (
    Class10Schema,
    Class12Schema,
    CollegeSchema,
)


# ============================================================
# COMMON EXTRACTION RULES
# ============================================================

_COMMON_RULES = """
GENERAL RULES:
- Read the entire document carefully.
- Extract ONLY information explicitly visible in the document.
- Never guess, infer, calculate, or correct values.
- Use the printed labels and table column headers to identify fields.
- If a field is missing, blank, unclear, or unreadable, return null.
- Empty marks, "-", "AB", "NA" or similar non-numeric entries must be null.
- Preserve names, IDs and text as printed.
- Keep dates in the format visible on the document.
- Do not confuse Roll No., Registration No., Enrollment No. and Serial No.
- Do not use information from the filename.
- Do not extract browser headers, URLs, timestamps or scan metadata.
- Read every row of the marks table.
- Do not merge information from different documents.
"""


# ============================================================
# CLASS 10
# ============================================================

_CLASS10_PROMPT = """
You are an academic document extraction system.

DOCUMENT TYPE:
Class 10 / Secondary / High School marksheet or certificate.

Extract the following information if explicitly printed.

CANDIDATE:
- name
- dob
- father_name
- mother_name
- gender

IDENTIFIERS:
- roll_no
- registration_no
- serial_no

ACADEMIC / INSTITUTION:
- board
- school
- institution_code
- academic_year
- passing_year
- exam_name

ADDRESS:
- address
- city
- district
- state
- pincode

RESULT:
- total_marks_obtained
- total_max_marks
- percentage
- result

MARKS:
For every subject row, use the subject name as the dictionary key.

For each subject extract:
- theory
- practical
- total
- max_marks

Read the table headers carefully:
- Theory / TH / Written → theory
- Practical / PR / IA → practical
- Total → total
- Maximum Marks / Max → max_marks

If a marks column is absent, use null.

IMPORTANT:
- Include every subject shown in the marks table.
- Do not calculate totals or percentages.
- Do not put maximum marks into obtained marks.
- Preserve subject names as printed.
- If duplicate subject names exist, use a unique key without losing either row.

EXTRA DETAILS:
Store other useful labelled information that does not fit the above fields in:
"extra_details": {}

Do not put marks-table rows inside extra_details.

Return ONLY valid JSON matching the provided schema.
"""


# ============================================================
# CLASS 12
# ============================================================

_CLASS12_PROMPT = """
You are an academic document extraction system.

DOCUMENT TYPE:
Class 12 / Senior Secondary / Intermediate marksheet or certificate.

Extract the following information if explicitly printed.

CANDIDATE:
- name
- dob
- father_name
- mother_name
- gender

IDENTIFIERS:
- roll_no
- registration_no
- serial_no

ACADEMIC / INSTITUTION:
- board
- school
- institution_code
- stream
- academic_year
- passing_year
- exam_name

ADDRESS:
- address
- city
- district
- state
- pincode

RESULT:
- total_marks_obtained
- total_max_marks
- percentage
- result

MARKS:
For every subject row, use the subject name as the dictionary key.

For each subject extract:
- theory
- practical
- total
- max_marks
- subject_type

COLUMN MAPPING:
- Theory / Written → theory
- Practical / PR / IA → practical
- Total / Obtained → total
- Maximum Marks / Max → max_marks
- Type → subject_type

If a column is absent, use null.

IMPORTANT:
- Include every subject shown in the marks table.
- Include additional/elective subjects if present.
- Do not calculate totals or percentages.
- Do not infer stream from subjects; extract it only if printed.
- Do not put maximum marks into obtained marks.
- Preserve subject names exactly as printed.
- If duplicate subject names exist, use a unique key without losing data.

EXTRA DETAILS:
Store other useful labelled information that does not fit the above fields in:
"extra_details": {}

Do not put marks-table rows inside extra_details.

Return ONLY valid JSON matching the provided schema.
"""


# ============================================================
# COLLEGE / UNIVERSITY
# ============================================================

_COLLEGE_PROMPT = """
You are an academic document extraction system.

DOCUMENT TYPE:
College / University marksheet, semester result, grade card or transcript.

Extract the following information if explicitly printed.

CANDIDATE:
- name
- dob
- father_name
- mother_name
- gender

IDENTIFIERS:
- roll_no
- registration_no
- enrollment_no
- serial_no

INSTITUTION:
- college
- university
- institution_code

PROGRAM:
- course
- course_code
- branch
- branch_code
- exam_name
- semester
- session
- academic_year
- passing_year

ADDRESS:
- address
- city
- district
- state
- pincode

RESULT:
- total_marks_obtained
- total_max_marks
- sgpa
- cgpa
- percentage
- result

MARKS:
For EVERY subject row, use the subject name as the dictionary key.

For each subject extract:
- subject_code
- subject_type
- internal
- external
- total
- max_marks
- grade
- grade_points
- credits

COLUMN MAPPING:
- Subject Code / Code → subject_code
- Type → subject_type
- Internal Obtained → internal
- External Obtained → external
- Total Obtained / Total → total
- Maximum Marks / Max → max_marks
- Grade / Letter Grade → grade
- Grade Point / Grade Points → grade_points
- Credit / Credits → credits

IMPORTANT:
- Read the column headers before reading the rows.
- Match values to their correct subject row.
- Include every subject, including grade-only subjects.
- Blank, "-", AB or NA marks must be null.
- Never calculate total, SGPA, CGPA or percentage.
- Never move internal/external marks between subjects.
- Never put maximum marks into obtained marks.
- Preserve subject names and codes as printed.
- If duplicate subject names exist, use a unique key without losing either row.

PROGRAM DETAILS:
- course: Extract the printed course/program name.
- course_code: Extract the printed course code.
- branch: Extract the printed branch/specialization.
- branch_code: Extract the printed branch code.
- exam_name: Extract the printed examination name.
- session: Extract the full session exactly as printed.
- academic_year: Extract the academic year if explicitly printed.
- passing_year: Extract the year of passing if explicitly printed.

SEMESTER HANDLING:

College result documents may show multiple semester references.

1. CURRENT SEMESTER:
Find the standalone field that explicitly identifies the current/result
semester, such as:
    "Semester : 6"
    "Semester : 4"
Extract that numeric value into:
    "semester"
Examples:
    "Semester : 6" → semester = 6
    "Semester : 4" → semester = 4

2. SEMESTERS COVERED:
A header may contain a combined value such as:
    "Semester : 5,6"
    "Semester : 3,4"
A combined value represents the semesters covered by the document.
It is NOT the current semester.
Store it in extra_details:
   "Semesters covered": "5,6"
or:
   "Semesters covered": "3,4"

3. WHEN BOTH EXIST:
If the document contains both:
   Header:    "Semester : 3,4"
   Detail:    "Semester : 4"
extract:
   "semester": 4
and:
   "extra_details": {"Semesters covered": "3,4"}
Similarly:
   Header:    "Semester : 5,6"
   Detail:    "Semester : 6"
must become:
   "semester": 6
and:
   "extra_details": {"Semesters covered": "5,6"}

4. PRIORITY:
The standalone/current-semester field has higher priority than a
combined semester value.

NEVER put "3,4", "5,6", etc. into the integer "semester" field.

If only a combined semester value is visible and no current semester
can be identified, return:
    "semester": null

and store the combined value in extra_details.

Do not infer the current semester from the combined value.
EXTRA DETAILS:
Store other useful labelled information that does not fit the above fields in:
"extra_details": {}

Examples:
- Total Subjects
- Total Credits
- Remarks
- Result Status
- Previous Semester SGPA
- Certification information

Do not put table rows inside extra_details.

Return ONLY valid JSON matching the provided schema.
"""


# ============================================================
# BUILD PROMPT
# ============================================================

def _schema_skeleton(schema_class, document_type):
   """
   Create a JSON skeleton directly from the Pydantic schema.
   """

   schema = {}
   for field_name, field in schema_class.model_fields.items():
      if field_name == "marks":
         schema[field_name] = {"SUBJECT_NAME": {}}
      elif field_name == "extra_details":
         schema[field_name] = {}
      elif field_name == "document_type":
         schema[field_name] = document_type
      else:
         schema[field_name] = None
   return json.dumps(schema,indent=2,ensure_ascii=False)


def build_extraction_prompt(document_type):
   if document_type == "10th_marksheet":
      prompt = _CLASS10_PROMPT
      schema = Class10Schema
      doc_type = "10th_marksheet"

   elif document_type == "12th_marksheet":
      prompt = _CLASS12_PROMPT
      schema = Class12Schema
      doc_type = "12th_marksheet"

   elif document_type == "college_marksheet":
      prompt = _COLLEGE_PROMPT
      schema = CollegeSchema
      doc_type = "college_marksheet"

   else:
      raise ValueError(f"Unsupported document type: {document_type}")

   skeleton = _schema_skeleton(schema,doc_type)

   return f"""
{prompt}

{_COMMON_RULES}

OUTPUT FORMAT:
Return ONLY one valid JSON object.

The JSON MUST follow this structure:

{skeleton}

Use:
- null for missing/unreadable scalar values
- {{}} for empty extra_details
- {{}} for an empty marks dictionary

Do not add fields that are not present in the schema.
Do not return markdown.
Do not explain your answer.
"""