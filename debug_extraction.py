"""
Diagnostic script — runs the extraction on an already-converted image and
prints the raw LLM JSON response plus every tier's resolution result.

Run from the project root:
    python debug_extraction.py
"""
import sys
import json
from pathlib import Path

# Add project root to path so imports work the same as main.py
sys.path.insert(0, str(Path(__file__).resolve().parent))

from extraction.vision_extractor import (
    encode_image, get_image_mime_type, build_extraction_prompt,
    extract_printed_percentage, extract_total_marks,
    calculate_subject_wise_percentage, resolve_percentage_from_record,
    client, MODEL,
)
from config.schemas import DocumentExtraction

IMAGE_PATH = r"converted_images\cand001\CLASS_10\page_1.jpg"
DOCUMENT_TYPE = "CLASS_10_MARKSHEET"

SEP = "=" * 70

def main():
    image_path = Path(IMAGE_PATH)
    if not image_path.exists():
        print(f"[ERROR] Image not found: {image_path}")
        return

    print(SEP)
    print(f"Image : {image_path}")
    print(f"Model : {MODEL}")
    print(SEP)

    encoded_image = encode_image(image_path)
    mime_type     = get_image_mime_type(image_path)
    prompt        = build_extraction_prompt(DOCUMENT_TYPE)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a precise document extraction system."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{encoded_image}"}},
                ],
            },
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )

    raw_content = response.choices[0].message.content
    print("\n-- RAW LLM JSON RESPONSE --")
    print(raw_content)

    # Parse
    data = json.loads(raw_content)
    print("\n-- PARSED JSON (pretty) --")
    print(json.dumps(data, indent=2, ensure_ascii=False))

    # Validate through Pydantic
    try:
        validated = DocumentExtraction(**data)
        result = validated.model_dump()
    except Exception as exc:
        print(f"\n[ERROR] Pydantic validation failed: {exc}")
        return

    print("\n-- PYDANTIC model_dump() --")
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))

    # Tier-by-tier diagnosis
    print("\n-- TIER DIAGNOSIS --")
    subjects = result.get("subjects", [])

    t1 = extract_printed_percentage(result)
    print(f"  Tier 1 (printed_percentage field) : {t1!r}")

    t2 = extract_total_marks(result)
    print(f"  Tier 2 (total_marks fraction)     : {t2!r}")

    t3 = calculate_subject_wise_percentage(subjects)
    print(f"  Tier 3 (subject-wise aggregation) : {t3!r}")

    pct, source = resolve_percentage_from_record(result, subjects)
    print(f"\n  RESOLVED percentage : {pct!r}")
    print(f"  RESOLVED source     : {source!r}")
    print(SEP)


if __name__ == "__main__":
    main()
