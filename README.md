# NIC Document AI System

A Python-based document-processing pipeline for Indian academic documents. The current pipeline scans candidate folders, converts the first page of PDFs to JPG, classifies the document with a vision model, extracts structured data with a document-type-specific prompt, validates the result with Pydantic, calculates derived percentage/CGPA values, generates a canonical name, evaluates cross-document identity confidence, and saves one JSON file per candidate.

## Current Pipeline

```text
Candidate Folder
      │
      ▼
Folder Walker
      │
      ▼
For each document
      │
      ├── PDF → first page → JPG
      │
      ├── Vision Classification
      │      └── 10th / 12th / College / Unknown
      │
      ├── Rename converted image
      │      ├── class10.jpg
      │      ├── class12.jpg
      │      └── cllg.jpg
      │
      ├── Type-specific Vision Extraction
      │
      ├── Pydantic Validation
      │      ├── Class10Schema
      │      ├── Class12Schema
      │      └── CollegeSchema
      │
      └── Store in candidate records
      │
      ▼
Percentage / CGPA Update
      │
      ▼
Canonical Final Name
      │
      ▼
Identity Confidence Score
      │
      ▼
output/<candidate_id>.json
```

## Input Structure

Candidates are organized as folders under `NIC/`:

```text
NIC/
├── cand001/
│   ├── 10.pdf
│   ├── 12.pdf
│   └── sem6.pdf
│
├── cand002/
│   ├── CLASS_10.pdf
│   ├── CLASS_12.pdf
│   └── 4.pdf
│
└── cand003/
    ├── 10th marksheet.pdf
    ├── 12th marksheet.pdf
    └── VI.pdf
```

The folder name becomes the `candidate_id`.

## Processing Details

### 1. Folder ingestion

`ingestion/folder_walker.py` scans the root folder, treats each immediate subfolder as a candidate, recursively finds supported files, and returns their paths.

### 2. PDF conversion

`extraction/pdf_converter.py` uses PyMuPDF to convert **only the first page** of a PDF into `page_1.jpg`.

Temporary page images are cleaned before conversion. After classification, the first image is renamed according to the detected document type:

```text
10th_marksheet   → class10.jpg
12th_marksheet   → class12.jpg
college_marksheet → cllg.jpg
```

The current pipeline intentionally ignores pages after page 1.

### 3. Vision classification

`classification/document_classifier.py` sends the first-page image to **Qwen 3.8 27B through Groq** and asks for exactly one of:

```text
10th_marksheet
12th_marksheet
college_marksheet
unknown
```

The classifier uses the `GROQ_API_KEY_2` environment variable in the current code.

### 4. Type-specific extraction

`extraction/prompt.py` builds a separate concise extraction prompt for each document type.

`extraction/vision_extractor.py` sends the classified image to **Qwen 3.8 27B through Groq** and validates the returned JSON against the corresponding Pydantic schema.

Extraction uses the `GROQ_API_KEY` environment variable in the current code.

The schemas are:

- `Class10Schema`
- `Class12Schema`
- `CollegeSchema`

Each schema contains document-level information plus a structured `marks` dictionary.

### 5. Percentage and CGPA

`verification/update_percentages.py` contains the current derived-field calculation.

For Class 10 and Class 12:

```text
percentage = sum(valid subject totals) / (number of valid subjects × 100) × 100
```

For college documents:

```text
percentage = sum(valid subject totals) / sum(subject max_marks) × 100
```

If a college subject does not contain `max_marks`, the current implementation uses `100` for that subject.

For college documents:

```text
cgpa = percentage / 10
```

Only subjects with a non-null `total` participate in the calculation.

### 6. Canonical name

`verification/consistency_checker.py` uses the name-variant knowledge base in `identity/names_variant.py` to generate `final_name`.

The original extracted `name` is preserved. `final_name` is added separately to every extracted document record.

### 7. Identity confidence

The same module calculates `identity_confidence_score` across all documents for a candidate.

Current fields and weights:

```text
name          → 50%
father_name   → 25%
mother_name   → 25%
```

Names are normalized through the variant knowledge base before comparison. Pairwise token-set Jaccard similarity is used for the field-level comparisons, followed by weighted averaging. The final score is limited to the range `0.0` to `1.0`.

## Output Structure

For each candidate, the pipeline writes:

```text
output/
├── cand001.json
├── cand002.json
└── cand003.json
```

Example structure:

```json
{
  "candidate_id": "cand001",
  "documents": {
    "class_10": [],
    "class_12": [],
    "college": []
  },
  "identity_confidence_score": 1.0
}
```

Each document can contain fields such as:

```text
name
final_name
dob
father_name
mother_name
roll_no
registration_no
enrollment_no
school / college
board / university
course / branch
semester / session
marks
percentage
cgpa / sgpa
result
extra_details
source_file
document_id
```

## Converted Image Structure

The current conversion output is organized by candidate:

```text
converted_images/
├── cand001/
│   ├── class10.jpg
│   ├── class12.jpg
│   └── cllg.jpg
│
├── cand002/
│   ├── class10.jpg
│   ├── class12.jpg
│   └── cllg.jpg
```

Only the first page of each PDF is currently used for classification and extraction.

## Setup

Create a virtual environment and install dependencies:

```bash
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root, at the same level as `main.py`.
The current active code uses **two Groq API keys**:

```env
GROQ_API_KEY=your_groq_extraction_api_key
GROQ_API_KEY_2=your_groq_classification_api_key
```

Key usage:

| Variable | Used by | Purpose |
|---|---|---|
| `GROQ_API_KEY` | `extraction/vision_extractor.py` | Qwen 3.8 27B document extraction |
| `GROQ_API_KEY_2` | `classification/document_classifier.py` | Qwen 3.8 27B document classification |

Keep the actual API keys private. Do not commit `.env` to Git. The `.env` file is already excluded by `.gitignore`.

Use the variable names exactly as shown. Extra variables such as `MINE_GROQ_API_KEY`, `MINE_GROQ_API_KEY_2`, or inactive OpenRouter settings are not required by the current active pipeline.

## Run

Place candidate folders under `NIC/` and run:

```bash
python main.py
```

The current entry point is CLI-based. The active processing pipeline does not start Django.

## Project Structure

```text
NIC_Document_AI/
│
├── main.py
│
├── classification/
│   └── document_classifier.py
│
├── config/
│   └── schemas.py
│
├── extraction/
│   ├── pdf_converter.py
│   ├── prompt.py
│   └── vision_extractor.py
│
├── identity/
│   └── names_variant.py
│
├── ingestion/
│   └── folder_walker.py
│
├── verification/
│   ├── consistency_checker.py
│   └── update_percentages.py
│
├── NIC/
│   └── <candidate folders>
│
├── converted_images/
├── output/
├── requirements.txt
└── README.md
```

## Module Map

| Module | Purpose |
|---|---|
| `main.py` | End-to-end CLI orchestration and JSON output |
| `ingestion/folder_walker.py` | Finds candidate folders and document files |
| `classification/document_classifier.py` | Vision-based document classification |
| `extraction/pdf_converter.py` | Converts the first PDF page to JPG |
| `extraction/prompt.py` | Builds 10th, 12th, and college extraction prompts |
| `extraction/vision_extractor.py` | Vision extraction + Pydantic validation |
| `config/schemas.py` | Document and marks Pydantic schemas |
| `verification/update_percentages.py` | Percentage and college CGPA calculation |
| `verification/consistency_checker.py` | Canonical name generation and identity confidence |
| `identity/names_variant.py` | Name variant knowledge base |

## Current Limitations

- Only the **first page** of each PDF is processed.
- Multi-page marksheets/transcripts are not merged yet.
- The current image pipeline processes PDF, JPG, JPEG, and PNG files. The folder walker also lists DOCX files, but `main.py` does not currently process DOCX files.
- Classification and extraction depend on Groq availability and rate limits.
- JSON extraction quality depends on the image quality and the vision model response.
- `identity_confidence_score` is based only on name, father's name, and mother's name.
- `final_name` is a canonical representation; the original extracted `name` remains unchanged.
- Django is present in the dependency list for the planned web layer, but the current executable pipeline is still `main.py`.

## Current Scope

The current working scope is:

```text
Folder ingestion
→ first-page PDF conversion
→ vision classification
→ type-specific vision extraction
→ schema validation
→ percentage / CGPA update
→ final_name generation
→ identity confidence
→ candidate JSON
```

The earlier report-generation, generic derivation-rule, and separate post-processing workflows are not part of the current active `main.py` pipeline.
