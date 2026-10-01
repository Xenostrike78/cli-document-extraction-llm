import os
import json
import base64
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

from .prompt import build_extraction_prompt
from config.schemas import (
    Class10Schema,
    Class12Schema,
    CollegeSchema,
)

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env file.")

client = Groq(api_key=api_key)
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

def extract_from_image(image_path, document_type):
    encoded_image = encode_image(image_path)
    mime_type = get_image_mime_type(image_path)

    prompt = build_extraction_prompt(document_type)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise document extraction system. "
                    "Extract only information explicitly visible "
                    "in the document. Never guess or infer."
                )
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
        temperature=0,
        max_tokens=900
    )


    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Model returned empty response.")

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Model returned invalid JSON: {exc}")
    
    # Validate according to document type
    if document_type == "10th_marksheet":
        validated = Class10Schema(**data)
    elif document_type == "12th_marksheet":
        validated = Class12Schema(**data)
    elif document_type == "college_marksheet":
        validated = CollegeSchema(**data)
    else:
        raise ValueError(f"Unsupported document type: {document_type}")

    print("DOCUMENT DATA EXTRACTING DONE..")

    return validated.model_dump()

# def extract_from_pdf(pdf_path, document_type, output_dir):
#     image_paths = convert_pdf_to_images(pdf_path, output_dir)
#     page_results = []
#     for page_number, image_path in enumerate(image_paths, start=1):
#         print(f"    Sending page {page_number} to Groq...\n\n")
#         result = extract_from_image(image_path, document_type)
#         page_results.append({
#             "page": page_number,
#             "image": str(image_path),
#             "data": result
#         })
#     return page_results
