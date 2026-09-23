"""
NIC Document AI System -- full pipeline orchestrator.

Input Documents -> Classification -> PDF Conversion -> AI Extraction
    -> Identity Resolution -> Derived Field Computation
    -> Cross-Document Consistency Check -> PDF Report

Run: python main.py
"""

from pathlib import Path

from ingestion.folder_walker import walk_candidates
from classification.document_classifier import classify_document
from extraction.vision_extractor import extract_from_image, extract_from_pdf
from derivation.rule_engine import compute_derived_fields, load_rules
from identity.resolver import resolve_candidate_identity
from verification.consistency_checker import run_consistency_check
from report.report_generator import generate_candidate_report

ROOT_FOLDER = "NIC"
CONVERTED_FOLDER = Path("converted_images")
REPORTS_FOLDER = Path("reports")


def extract_candidate_records(candidate: dict) -> dict:
    """
    Runs classification + extraction for every file in a candidate's
    folder. Returns {doc_type: extracted_record_dict}. When a
    document type appears more than once (e.g. two scans of the same
    marksheet), the last extraction wins and a note is printed --
    duplicates are a data-hygiene issue for the human reviewer, not
    something this stage should silently merge.
    """
    candidate_id = candidate["candidate_id"]
    records = {}

    for file_info in candidate["files"]:
        file_path = Path(file_info["path"])
        print(f"  Processing: {file_path.name}")

        document_type = classify_document(file_path)
        if document_type == "unknown":
            print(f"    Unknown document type -- skipped: {file_path.name}")
            continue

        suffix = file_path.suffix.lower()
        try:
            if suffix == ".pdf":
                output_dir = CONVERTED_FOLDER / candidate_id / file_path.stem
                page_results = extract_from_pdf(file_path, document_type, output_dir)
                # Use the first page's extraction as the document-level record.
                # Multi-page marksheets with subject tables on later pages would
                # need a merge step here -- left as a documented extension point.
                record = page_results[0]["data"] if page_results else None
            elif suffix in {".jpg", ".jpeg", ".png"}:
                record = extract_from_image(file_path, document_type)
            else:
                print(f"    Unsupported file for vision extraction: {file_path.name}")
                continue
        except Exception as exc:
            print(f"    Extraction failed for {file_path.name}: {exc}")
            continue

        if record is None:
            continue

        if document_type in records:
            print(f"    Note: multiple files classified as '{document_type}' -- using latest")
        records[document_type] = record

    return records


def process_candidate(candidate: dict, rules: dict):
    candidate_id = candidate["candidate_id"]
    print("\n" + "=" * 70)
    print(f"Candidate: {candidate_id}")
    print("=" * 70)

    records = extract_candidate_records(candidate)

    self_reported = candidate.get("self_reported") or {}
    if self_reported:
        records["self_reported"] = self_reported
    else:
        print("  No self_reported.json found -- self-reported fields will show as MISSING.")

    if not records:
        print("  No usable documents for this candidate. Skipping report.")
        return

    # Derived fields computed per document (percentage from CGPA,
    # annual income from monthly income, etc.), then folded back into
    # each record so consistency checks compare like-for-like values.
    derived_by_doc = {}
    for doc_type, record in records.items():
        derived = compute_derived_fields(record, rules)
        derived_by_doc[doc_type] = derived
        for field_name, info in derived.items():
            if info["value"] is not None:
                record[field_name] = info["value"]

    identity_results = resolve_candidate_identity(records) if len(records) > 1 else []
    consistency_results = run_consistency_check(records, identity_results)

    output_path = REPORTS_FOLDER / f"{candidate_id}_report.pdf"
    generate_candidate_report(
        candidate_id=candidate_id,
        records=records,
        derived_by_doc=derived_by_doc,
        consistency_results=consistency_results,
        identity_results=identity_results,
        output_path=output_path,
    )
    print(f"  Report generated: {output_path}")


def main():
    rules = load_rules()
    candidates = walk_candidates(ROOT_FOLDER)

    if not candidates:
        print("No candidate folders/documents found under 'NIC/'.")
        return

    for candidate in candidates:
        process_candidate(candidate, rules)

    print("\nAll candidates processed. Reports are in the 'reports/' folder.")


if __name__ == "__main__":
    main()
