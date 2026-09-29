# NIC Document Cross-Verification System

A Python pipeline that processes candidate document folders, extracts structured data using the Groq vision API, checks identity consistency across documents, and generates a PDF report per candidate.

## How it works

```
NIC/<candidate_id>/
  ├── CLASS_10.pdf
  ├── CLASS_12.pdf
  └── self_reported.json  (optional)
```

For each candidate folder:
1. **Classify** — figures out what each file is (10th marksheet, 12th marksheet, etc.) based on the filename
2. **Convert** — PDFs are converted to JPG page images using PyMuPDF
3. **Extract** — each page image is sent to Groq's vision model; structured JSON is returned
4. **Resolve identity** — compares DOB, parent names, and the candidate name across documents to check they're the same person
5. **Derive fields** — calculates percentage, annual income, etc. using rules defined in `config/rules.json`
6. **Check consistency** — field-by-field comparison across all documents (MATCH / MISMATCH / MISSING / LOW_CONFIDENCE)
7. **Generate report** — everything above goes into a PDF at `reports/<candidate_id>_report.pdf`

## Setup

```bash
pip install -r requirements.txt
```

Add your Groq API key to `.env`:
```
GROQ_API_KEY=your_key_here
```

Put candidate documents in `NIC/<candidate_id>/` (PDFs or images).

Optionally add `NIC/<candidate_id>/self_reported.json` with what the candidate claimed:
```json
{
  "name": "Faraz Khan",
  "father_name": "Mohd Sajid Khan",
  "dob": "01-01-2005",
  "percentage": 87.6
}
```
Any field can be omitted — missing fields show as `MISSING` in the report, not as errors.

## Run

```bash
python main.py
```

Reports are saved to `reports/<candidate_id>_report.pdf`.

## Module map

| What it does | File |
|---|---|
| Walk candidate folders, load self-reported JSON | `ingestion/folder_walker.py` |
| Classify documents by filename | `classification/document_classifier.py` |
| Convert PDFs to images | `extraction/pdf_converter.py` |
| Send images to Groq, parse JSON | `extraction/vision_extractor.py` |
| Normalize and compare names | `identity/name_matcher.py` |
| Indian name variant dictionary (Mohd → Mohammad, etc.) | `identity/indian_names_kb.py` |
| TF-IDF fallback for rare name variants | `identity/name_rag.py` |
| Decide if documents belong to the same person | `identity/resolver.py` |
| Compute derived fields (percentage, income) | `derivation/rule_engine.py` + `config/rules.json` |
| Cross-document field consistency | `verification/consistency_checker.py` |
| Build PDF report | `report/report_generator.py` |

## Identity resolution

The resolver checks documents in this order:

1. **Hard fields first** — DOB, father's name, mother's name. If these contradict, it's flagged as a likely non-match regardless of the name.
2. **Name last** — name matching runs after the field comparison to confirm or challenge the initial verdict. It handles Indian name variants (Md, Mohd, Mohammad) using a knowledge base + TF-IDF fallback.
3. **Overall verdict** — the PDF shows a single plain-English conclusion: same entity / not same entity / needs review.

Enrollment numbers are intentionally excluded from cross-document comparison since they differ between 10th and 12th boards.

## 12th class percentage

For 12th marksheets specifically, percentage is calculated only from recognized CBSE academic subjects (English, Physics, Chemistry, Mathematics, etc.). Co-scholastic subjects like Work Experience and Health & Physical Education are excluded.

## Known limitations

- **Classification is filename-based.** Files with non-descriptive names (e.g. `scan1.jpg`) will be skipped as `unknown`.
- **Multi-page PDFs:** only the first page's data is used per document. If marks tables span multiple pages, a merge step would need to be added.
- **Groq rate limits:** on the free tier, `max_tokens` is capped per request. If extraction fails with a 429 error, the limit is already set in `vision_extractor.py`.
