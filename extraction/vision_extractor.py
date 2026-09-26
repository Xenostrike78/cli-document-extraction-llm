import os
import json
import base64
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

from config.schemas import DocumentExtraction
from extraction.pdf_converter import convert_pdf_to_images

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env file.")

client = Groq(api_key=api_key)
# MODEL = "llama-3.1-8b-instant"
MODEL = "qwen/qwen3.8-27b"

def encode_image(image_path):
    print("encode_image\n")
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def get_image_mime_type(image_path):
    suffix = Path(image_path).suffix.lower()
    print("image mime type \n")
    if suffix in {".jpg", ".jpeg"}:
        print(suffix,"\n")
        return "image/jpeg"
    if suffix == ".png":
        print(suffix,"\n")
        return "image/png"
    raise ValueError(f"Unsupported image type: {suffix}")

def build_extraction_prompt(document_type):
    return f'''
You are a highly accurate document data extraction system for academic
certificates, marksheets, scorecards, and educational documents.

Document type: {document_type}

Your task is to extract information from the visible document and assign
each value to the CORRECT SEMANTIC FIELD.

==================================================
IMPORTANT: SEMANTIC EXTRACTION
==================================================

DO NOT assign a value to a field merely because it looks like the expected
data type.

For every value, first determine:

1. What does the value represent?
2. What label is associated with it?
3. What section/table does it belong to?
4. Is the association clear from the document?

If the meaning of a value is unclear, return null instead of guessing.

==================================================
1. NAME
==================================================

Extract the student's name only from the student's name field or an
unambiguous statement identifying the student.

Examples:

"This is to certify that FARAZ KHAN"
→ name = "FARAZ KHAN"

Do not confuse the student's name with:
- Father's name
- Mother's name
- Guardian's name
- School name
- Teacher/examiner name
- Principal name
- Controller of Examination name

Preserve the name exactly as written.

==================================================
2. DATE OF BIRTH
==================================================

This is a CRITICAL field.

Only extract a value as `dob` if the document explicitly identifies
that value as the student's Date of Birth.

Acceptable labels include:

- Date of Birth
- DOB
- D.O.B.
- Birth Date
- जन्म तिथि

The date must be clearly associated with one of these labels.

DO NOT assume that every date on the document is DOB.

NEVER use the following as DOB unless explicitly labelled as DOB:

- Date printed near the student's photograph
- Photograph date
- Photo capture date
- Certificate issue date
- Document date
- Examination date
- Result date
- Printing date
- Scanning date
- Admission date
- Registration date
- Academic session date
- Any unrelated date appearing elsewhere

For example, if the photograph contains:

FARAZ KHAN
04-11-2020

DO NOT set:

"dob": "04-11-2020"

unless the document explicitly identifies 04-11-2020 as the Date of Birth.

If no clearly labelled DOB exists:

"dob": null

NEVER infer DOB from age, examination year, registration number,
photograph, or any other information.

==================================================
3. FATHER / GUARDIAN NAME
==================================================

Extract the value according to its label.

Examples:

"Father's Name MOHD SAJID KHAN"
→ father_name = "MOHD SAJID KHAN"

"Father's / Guardian's Name MOHD SAJID KHAN"
→ father_name = "MOHD SAJID KHAN"

Do not confuse father's/guardian's name with the student's name or
mother's name.

==================================================
4. MOTHER'S NAME
==================================================

Extract only when explicitly associated with:

- Mother's Name
- Mother Name
- माता का नाम

Do not infer the mother's name from any other source.

If absent:

"mother_name": null

==================================================
5. ROLL NUMBER
==================================================

Extract only the value associated with:

- Roll No.
- Roll Number
- रोल नंबर

Do not confuse it with:

- Registration number
- Certificate number
- School code
- Centre code
- Admission number
- Subject code
- Candidate ID

Preserve the value exactly as written.

==================================================
6. REGISTRATION NUMBER
==================================================

If a registration number is present, extract it separately.

Do not confuse registration number with roll number.

==================================================
7. DOCUMENT DATE
==================================================

If the document contains a date that clearly refers to the document,
certificate, or marksheet itself, store it as `document_date`.

Examples:

"Dated : 22-07-2022"
"Date of Issue : 22-07-2022"

→ document_date = "22-07-2022"

A document date MUST NOT be stored as `dob`.

If the date has no clear semantic association, do not assign it to DOB.

==================================================
8. PERCENTAGE
==================================================

Extract percentage ONLY if it is explicitly printed as a percentage
in the document.

Examples:

"Percentage: 86.4%"
"86.4%"

Do NOT calculate percentage from marks.

If percentage is not explicitly printed:

"percentage": null

==================================================
9. CGPA
==================================================

Extract CGPA only when it is explicitly present and clearly labelled.

Do NOT calculate CGPA from marks.

If CGPA is not present:

"cgpa": null

==================================================
10. RESULT
==================================================

Extract the official result exactly as shown.

Examples:

PASS
FAIL
COMPARTMENT

Do not infer result from marks.

==================================================
11. SUBJECT-WISE MARKS
==================================================

This is a CRITICAL section.

Read the marks table according to its actual ROWS and COLUMNS.

For every subject, extract:

- subject_name
- subject_code
- theory_marks
- practical_marks
- total_marks

The relationship must be:

SUBJECT CODE
        ↓
SUBJECT NAME
        ↓
THEORY MARKS
        ↓
PRACTICAL / INTERNAL MARKS
        ↓
TOTAL MARKS

Read the table horizontally by row.

Example:

301 | ENGLISH CORE | 072 | 020 | 092

must become:

{{
  "subject_name": "ENGLISH CORE",
  "subject_code": "301",
  "theory_marks": 72,
  "practical_marks": 20,
  "total_marks": 92
}}

Do NOT take numbers simply because they are visually close to a subject.

Always determine their column position.

==================================================
12. MISSING MARKS
==================================================

If a subject has no visible theory marks:

"theory_marks": null

If a subject has no visible practical marks:

"practical_marks": null

If a subject has no visible total:

"total_marks": null

Do NOT replace missing values with 0.

Do NOT invent marks.

==================================================
13. MARKS VALIDATION
==================================================

Do not alter marks printed in the document.

If:

theory = 72
practical = 20
total = 92

extract them exactly.

If the arithmetic does not match, preserve the document values rather
than modifying them.

==================================================
14. PHOTO / IMAGE AREA
==================================================

Treat text appearing inside or immediately around a student's photograph
with caution.

A photograph may contain:

- Photograph date
- Photo ID
- Camera date
- Printing date
- Other unrelated numbers

Do NOT automatically treat such information as personal information.

In particular:

A date near the photograph is NOT DOB unless explicitly labelled as DOB.

==================================================
15. NO GUESSING
==================================================

Never:

- Guess missing information
- Infer DOB
- Calculate percentage
- Calculate CGPA
- Invent marks
- Convert unrelated dates into DOB
- Treat OCR noise as valid data
- Merge unrelated numbers
- Move marks between subjects
- Assume a value belongs to a field without clear evidence

When uncertain, return null.

==================================================
16. OUTPUT
==================================================

Return ONLY valid JSON.

Use exactly this structure:

{{
  "document_type": "{document_type}",
  "name": null,
  "dob": null,
  "father_name": null,
  "mother_name": null,
  "guardian_name": null,
  "roll_no": null,
  "registration_no": null,
  "school": null,
  "document_date": null,
  "percentage": null,
  "cgpa": null,
  "result": null,
  "subjects": [
    {{
      "subject_name": null,
      "subject_code": null,
      "theory_marks": null,
      "practical_marks": null,
      "total_marks": null
    }}
  ]
}}

==================================================
FINAL CHECK BEFORE RETURNING JSON
==================================================

Before producing the final JSON, verify:

1. Is DOB explicitly labelled?
   If NO → dob = null.

2. Is a date associated with the document/certificate?
   If YES → document_date.

3. Is a date located near the photograph?
   If YES → do NOT assume it is DOB.

4. Are student's, father's, mother's and guardian's names correctly
   associated with their labels?

5. Is the roll number actually labelled "Roll No."?

6. Is registration number kept separate from roll number?

7. Are subject codes mapped to the correct subjects?

8. Are theory, practical and total marks mapped according to the
   correct table columns?

9. Are missing marks represented as null rather than 0?

10. Was percentage calculated?
    If YES → remove it and return null unless explicitly printed.

11. Was CGPA calculated?
    If YES → remove it and return null unless explicitly printed.

12. Did you infer any information?
    If YES → remove the inferred value.

Return ONLY the JSON.
'''


# def build_extraction_prompt(document_type):
#     return f'''
# You are a precise document extraction system.

# Document type: {document_type}

# Extract information ONLY from the visible document.

# Rules:
# 1. Do not guess.
# 2. Do not infer missing values.
# 3. If a field is not visible, return null.
# 4. Preserve names exactly as written.
# 5. Preserve roll numbers exactly.
# 6. Read dates carefully.
# 7. Do not confuse marks with percentages.
# 8. Do not calculate percentage.
# 9. Extract subject-wise marks when visible.
# 10. If a father's/guardian's name is printed on the document, extract it.
# 11. If an income figure is printed, extract it as monthly_income or
#     annual_income exactly as labelled on the document -- do not convert
#     between the two yourself.
# 12. Return valid JSON only.

# Return exactly this structure:
# {{
#   "document_type": "{document_type}",
#   "name": null,
#   "father_name": null,
#   "dob": null,
#   "roll_no": null,
#   "percentage": null,
#   "cgpa": null,
#   "monthly_income": null,
#   "annual_income": null,
#   "result": null,
#   "subjects": [
#     {{
#       "subject_name": null,
#       "subject_code": null,
#       "theory_marks": null,
#       "practical_marks": null,
#       "total_marks": null
#     }}
#   ]
# }}
# '''

def extract_from_image(image_path, document_type):
    encoded_image = encode_image(image_path)
    mime_type = get_image_mime_type(image_path)
    prompt = build_extraction_prompt(document_type)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a precise document extraction system."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{encoded_image}"
                        }
                    }
                ]
            }
        ],
        response_format={"type": "json_object"},
        temperature=0
    )

    content = response.choices[0].message.content
    data = json.loads(content)
    validated = DocumentExtraction(**data)
    return validated.model_dump()

def extract_from_pdf(pdf_path, document_type, output_dir):
    image_paths = convert_pdf_to_images(pdf_path, output_dir)
    page_results = []
    for page_number, image_path in enumerate(image_paths, start=1):
        print(f"    Sending page {page_number} to Groq...\n\n")
        result = extract_from_image(image_path, document_type)
        page_results.append({
            "page": page_number,
            "image": str(image_path),
            "data": result
        })
    return page_results
