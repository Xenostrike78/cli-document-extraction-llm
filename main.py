"""
NIC Document AI System -- full pipeline orchestrator.

Input Documents -> Classification -> PDF Conversion -> AI Extraction
    -> Identity Resolution -> Derived Field Computation
    -> Cross-Document Consistency Check -> PDF Report

Run: python main.py
"""

from pathlib import Path
import json,os
from ingestion.folder_walker import walk_candidates
from classification.document_classifier import classify_document,classify_image
from extraction.pdf_converter import convert_pdf_to_images
from extraction.vision_extractor import extract_from_image
from derivation.rule_engine import compute_derived_fields, load_rules
from identity.resolver import resolve_candidate_identity
from verification.consistency_checker import run_consistency_check
from report.report_generator import generate_candidate_report

BASE_DIR = Path(__file__).resolve().parent

ROOT_FOLDER = BASE_DIR / "NIC"
CONVERTED_FOLDER = BASE_DIR / "converted_images"
OUTPUT_FOLDER = BASE_DIR / "output"
REPORTS_FOLDER = BASE_DIR / "reports"

IMAGE_EXTENSIONS = {".jpg",".jpeg",".png"}

def extract_candidate_records(candidate: dict) -> dict:
    """
    Process every document belonging to a candidate.

    Pipeline:

        PDF
          -> JPG pages
          -> Vision classification
          -> Type-specific extraction

        Image
          -> Vision classification
          -> Type-specific extraction

    Returns:

        {
            "10th_marksheet": [...],
            "12th_marksheet": [...],
            "college_marksheet": [...]
        }

    Each document type contains a list because a candidate may have
    multiple documents of the same type.
    """
    candidate_id = candidate["candidate_id"]
    records = {
        "class_10": [],
        "class_12": [],
        "college": [],
    }

    for file_info in candidate["files"]:
        file_path = Path(file_info["path"])
        print("\n" + "-" * 70)
        print(f"Processing: {file_path.name}")
        print("-" * 70)

        suffix = file_path.suffix.lower()
        try:
            # ========================================================
            # STEP 1: CONVERT PDF TO JPG
            # ========================================================
            if suffix == ".pdf":
                # output_dir = (CONVERTED_FOLDER/ candidate_id/ file_path.stem)
                output_dir = CONVERTED_FOLDER/ candidate_id
                print("  PDF detected.")
                print("  Converting PDF pages to JPG...")
                
                image_paths = convert_pdf_to_images(file_path,output_dir)
                
                if not image_paths:
                    print("  No pages generated. Skipping.")
                    continue

            elif suffix in IMAGE_EXTENSIONS:
                image_paths = [file_path]
            else:
                print(f"  Unsupported file type: {file_path.suffix}")
                continue

            # ========================================================
            # STEP 2: CLASSIFY DOCUMENT USING VISION
            # ========================================================

            first_page = image_paths[0]
            print(f"  Classifying document from: "f"{first_page.name}")

            document_type = classify_image(first_page)
            print(f"  Document type: {document_type}")

            if document_type == "unknown":
                print("  Could not determine document type. ""Skipping document.")
                continue

            
            # IMAGE SAVED
            if suffix == ".pdf":
                output_names = {
                    "10th_marksheet": "class10.jpg",
                    "12th_marksheet": "class12.jpg",
                    "college_marksheet": "cllg.jpg",
                }
                new_name = output_names[document_type]
                final_image_path = (CONVERTED_FOLDER/ candidate_id/ new_name)
                first_page.rename(final_image_path)
                first_page = final_image_path
                print(f"  Converted image saved as: "f"{first_page}")
            
            # ========================================================
            # STEP 3: TYPE-SPECIFIC EXTRACTION
            # ========================================================
            
            print(f"  Extracting first page: {first_page.name}...")
            record = extract_from_image(first_page,document_type)
            
            record["document_id"] = (
                f"{candidate_id}_{file_path.stem}"
            )

            record["source_file"] = file_path.name

            # ========================================================
            # STEP 6: STORE IN CORRECT DOCUMENT BUCKET
            # ========================================================

            if document_type == "10th_marksheet":
                records["class_10"].append(record)
            elif document_type == "12th_marksheet":
                records["class_12"].append(record)
            elif document_type == "college_marksheet":
                records["college"].append(record)
            else:
                print(f"  Unsupported classified type: "f"{document_type}")


        except Exception as exc:
            print(f"    Extraction failed for {file_path.name}: {exc}")
            continue

        # if record is None:
        #     continue

        # if document_type in records:
        #     print(f"    Note: multiple files classified as '{document_type}' -- using latest")
        # records[document_type] = record

    return records


def process_candidate(candidate: dict, rules: dict):
    candidate_id = candidate["candidate_id"]
    print("\n" + "=" * 70)
    print(f"Candidate: {candidate_id}")
    print("=" * 70)

    records = extract_candidate_records(candidate)


    # ================================================================
    # SELF REPORTED DATA
    # ================================================================

    # self_reported = candidate.get("self_reported") or {}
    # if self_reported:
        # records["self_reported"] = self_reported
    # else:
        # print("  No self_reported.json found -- self-reported fields will show as MISSING.")
    
    # Check whether there is anything useful
    documents_found = (records["class_10"] or records["class_12"] or records["college"])

    if not documents_found:
        print("  No usable documents for this candidate.")
        return

    # Build final candidate JSON
    candidate_output = {
        "candidate_id": candidate_id,
        "documents": {
            "class_10": records["class_10"],
            "class_12": records["class_12"],
            "college": records["college"],
        },
    }

    # Save JSON
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    output_path = OUTPUT_FOLDER / f"{candidate_id}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            candidate_output,
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"\n  JSON saved: {output_path}")

    '''
    if not records:
        print("  No usable documents for this candidate. Skipping report.")
        return

    # ================================================================
    # DERIVED FIELDS
    # ================================================================

    derived_by_doc = {}

    for doc_group in ("class_10","class_12","college",):
        for record in records[doc_group]:
            derived = compute_derived_fields(record,rules)
            derived_by_doc.setdefault(doc_group,[]).append(derived)
            for field_name, info in derived.items():
                if info["value"] is not None:
                    record[field_name] = info["value"]


    # IDENTITY RESOLUTION
    identity_results = resolve_candidate_identity(records)

    #CONSISTENCY CHECK
    consistency_results = run_consistency_check(records,identity_results)

    #REPORT
    REPORTS_FOLDER.mkdir(parents=True,exist_ok=True)

    output_path = (REPORTS_FOLDER/ f"{candidate_id}_report.pdf")

    generate_candidate_report(
        candidate_id=candidate_id,
        records=records,
        derived_by_doc=derived_by_doc,
        consistency_results=consistency_results,
        identity_results=identity_results,
        output_path=output_path,
    )

    print(f"  Report generated: {output_path}")
    '''


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
