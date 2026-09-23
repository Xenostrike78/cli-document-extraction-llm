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
You are a precise document extraction system.

Document type: {document_type}

Extract information ONLY from the visible document.

Rules:
1. Do not guess.
2. Do not infer missing values.
3. If a field is not visible, return null.
4. Preserve names exactly as written.
5. Preserve roll numbers exactly.
6. Read dates carefully.
7. Do not confuse marks with percentages.
8. Do not calculate percentage.
9. Extract subject-wise marks when visible.
10. If a father's/guardian's name is printed on the document, extract it.
11. If an income figure is printed, extract it as monthly_income or
    annual_income exactly as labelled on the document -- do not convert
    between the two yourself.
12. Return valid JSON only.

Return exactly this structure:
{{
  "document_type": "{document_type}",
  "name": null,
  "father_name": null,
  "dob": null,
  "roll_no": null,
  "percentage": null,
  "cgpa": null,
  "monthly_income": null,
  "annual_income": null,
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
'''

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
