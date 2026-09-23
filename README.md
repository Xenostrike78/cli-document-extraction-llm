# NIC Document Cross-Verification System

Full pipeline:
```
NIC/<cand>/ (PDF/JPG docs + optional self_reported.json)
  -> Document Classification
  -> PDF -> JPG Conversion (PyMuPDF)
  -> Groq Vision Extraction -> structured JSON
  -> Identity Resolution (name matching + DOB/roll/father corroboration + LLM fallback)
  -> Derived Field Computation (config/rules.json)
  -> Cross-Document Consistency Check (MATCH/MISMATCH/MISSING/LOW_CONFIDENCE/RESOLVED_VARIANT)
  -> Per-candidate PDF report (reports/<cand>_report.pdf)
```

## Setup
1. `pip install -r requirements.txt`
2. `.env` already has `GROQ_API_KEY` set (rotate it before any public use).
3. Put candidate documents under `NIC/<candidate_id>/` (PDFs and/or images).
4. Optionally add `NIC/<candidate_id>/self_reported.json` with the candidate's
   own declared values -- compared against what the AI extracts. Fields:
   `name`, `father_name`, `dob`, `roll_no`, `percentage`, `cgpa`,
   `monthly_income`, `annual_income`. Any subset is fine; missing fields
   are reported as `MISSING`, not treated as errors.

## Run
```
python main.py
```
Reports are written to `reports/<candidate_id>_report.pdf`.

## Module map
| Stage | Module |
|---|---|
| Folder walk + self-reported form loading | `ingestion/folder_walker.py` |
| Document type classification (filename heuristics) | `classification/document_classifier.py` |
| PDF -> JPG | `extraction/pdf_converter.py` |
| Vision extraction (Groq) | `extraction/vision_extractor.py` |
| Name normalization + fuzzy matching | `identity/name_matcher.py` |
| Identity resolution (name + DOB + roll + father + LLM fallback) | `identity/resolver.py` |
| Derived field rules | `config/rules.json`, `derivation/rule_engine.py` |
| Cross-document consistency check | `verification/consistency_checker.py` |
| PDF report generation | `report/report_generator.py` |

## Notes on current scope
- **Document classification** is filename-based (regex), as in the original
  code. If candidates upload inconsistently named scans (e.g. `scan1.jpg`),
  classification will return `unknown` and the file is skipped -- a
  content-based classifier (first-page vision call) is the natural next
  upgrade, not yet built.
- **Multi-page marksheets**: only the first page's extraction is used as
  the document-level record. If subject-wise tables commonly span multiple
  pages, a merge step should be added in `main.py::extract_candidate_records`.
- **LLM adjudication** (`identity/resolver.py::llm_adjudicate`) only fires
  for genuinely borderline name-similarity cases with no corroborating
  field (rare) -- it reuses the same Groq key, no extra setup needed.
- **RAG** is intentionally excluded per your instruction, and the frontend
  is out of scope for this delivery -- this is a script you run over a
  `NIC/` folder and get PDF reports out of.
