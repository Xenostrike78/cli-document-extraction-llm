# NIC Document Cross-Verification System

A Python pipeline that processes candidate document folders, extracts structured data using the Groq vision API, computes derived fields (percentage, CGPA), evaluates cross-document identity confidence, and outputs a structured JSON per candidate.

## How it works

```
NIC/<candidate_id>/
  ├── CLASS_10.pdf
  ├── CLASS_12.pdf
  └── COLLEGE.pdf   (or .jpg / .png)
```

For each candidate folder:
1. **Classify** — the first page of each file is sent to the vision model to determine its document type (`10th_marksheet`, `12th_marksheet`, `college_marksheet`, or `unknown`)
2. **Convert** — PDFs are converted to JPG page images using PyMuPDF
3. **Extract** — each classified page image is sent to Groq's vision model; structured JSON is returned with fields like `name`, `marks`, `father_name`, `mother_name`, etc.
4. **Derive fields** — `percentage` and `cgpa` are calculated automatically:
   - For school marksheets: `percentage = (sum of subject totals / n × 100) × 100`
   - For college marksheets: `percentage = (sum of subject totals / sum of max_marks) × 100`, `cgpa = percentage / 10`
   - Subjects with `total: null` are ignored
5. **Evaluate identity** — an `identity_confidence_score` (0.0 – 1.0) is computed from `name`, `father_name`, and `mother_name` across all documents using canonical name resolution and token-set Jaccard similarity
6. **Output JSON** — all extracted data, computed fields, and identity score are written to `output/<candidate_id>.json`

## Output structure

```json
{
  "candidate_id": "cand001",
  "documents": {
    "class_10": [ { ... } ],
    "class_12": [ { ... } ],
    "college":  [ { ... } ]
  },
  "identity_confidence_score": 0.95
}
```

Each document record includes:
- Extracted fields: `name`, `father_name`, `mother_name`, `dob`, `roll_no`, `marks`, `percentage`, `cgpa`, etc.
- `final_name` — canonical form of the name after variant resolution (e.g. `Mohd.` → `mohammad`)
- `source_file` — original filename

## Identity confidence score

The `identity_confidence_score` is a float between `0.0` and `1.0`:

| Score range | Interpretation |
|---|---|
| 0.90 – 1.00 | Strong match — documents almost certainly belong to the same person |
| 0.70 – 0.89 | Likely match — minor naming variations present |
| 0.50 – 0.69 | Uncertain — manual review recommended |
| 0.00 – 0.49 | Likely mismatch — documents probably belong to different people |

**How it is calculated:**

1. Each name field (`name`, `father_name`, `mother_name`) across all documents is resolved to its canonical form using `identity/names_variant.py` (handles `Mohd` → `mohammad`, `Md.` → `mohammad`, etc.)
2. Pairwise **Token-Set Jaccard Similarity** is computed:
   ```
   score = |words(A) ∩ words(B)| / |words(A) ∪ words(B)|
   ```
3. The three field scores are aggregated with weighted averaging:
   - **Name**: 50%
   - **Father's Name**: 25%
   - **Mother's Name**: 25%
4. Missing fields are skipped and their weight is redistributed proportionally.

## Setup

```bash
pip install -r requirements.txt
```

Add your Groq API key to `.env`:
```
GROQ_API_KEY=your_key_here
```

Put candidate documents in `NIC/<candidate_id>/` (PDFs or images).

## Run

```bash
python main.py
```

Output JSONs are saved to `output/<candidate_id>.json`.

To recompute identity scores for existing JSON files without re-running the full pipeline:
```bash
python -m verification.consistency_checker
```

## Module map

| What it does | File |
|---|---|
| Walk candidate folders | `ingestion/folder_walker.py` |
| Classify document type using vision | `classification/document_classifier.py` |
| Convert PDFs to images | `extraction/pdf_converter.py` |
| Send images to Groq, parse JSON | `extraction/vision_extractor.py` |
| Normalize and compare names | `identity/name_matcher.py` |
| Indian name variant dictionary | `identity/names_variant.py` |
| TF-IDF fallback for rare name variants | `identity/name_rag.py` |
| Decide if documents belong to the same person | `identity/resolver.py` |
| Compute derived fields (percentage, CGPA) | `verification/update_percentages.py` |
| Cross-document consistency + identity score | `verification/consistency_checker.py` |
| Derivation rule engine | `derivation/rule_engine.py` + `config/rules.json` |

## Percentage & CGPA calculation rules

| Document type | Max marks per subject | CGPA |
|---|---|---|
| `10th_marksheet` | 100 (fixed) | Not calculated |
| `12th_marksheet` | 100 (fixed) | Not calculated |
| `college_marksheet` | Uses `max_marks` field from extracted data | `percentage / 10` |

Subjects where `total` is `null` are excluded from the calculation.

## Known limitations

- **Classification is vision-based.** Unusual or unclear document layouts may be misclassified.
- **Multi-page PDFs:** only the first page's data is used per document. If marks tables span multiple pages, a merge step would need to be added.
- **Groq rate limits:** on the free tier, `max_tokens` is capped per request. If extraction fails with a 429 error, the limit is already set in `vision_extractor.py`.
- **Identity score requires multiple documents.** If a candidate has only one document, all fields score `1.0` by default (nothing to compare against).
