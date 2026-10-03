import base64
import json,os
from pathlib import Path
from openai import OpenAI
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

'''
# OPEN_MODEL = "qwen/qwen3.8-27b:free"
OPEN_MODEL = "google/gemma-4-31b-it:free"
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

if not openrouter_api_key:
    raise RuntimeError("OPENROUTER_API_KEY is not set. Add it to your .env file.")

open_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=openrouter_api_key,
)

'''
api_key_2 = os.getenv("GROQ_API_KEY_2")

if not api_key_2:
    raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env file.")

client = Groq(api_key=api_key_2)
MODEL = "qwen/qwen3.8-27b"
# '''

def classify_image(image_path: Path) -> str:
    """
    Classify an academic document into:
        - 10th_marksheet
        - 12th_marksheet
        - college_marksheet
        - unknown
    """

    # Read image
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

    # Determine MIME type
    suffix = image_path.suffix.lower()

    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }

    mime_type = mime_types.get(suffix)

    if not mime_type:
        raise ValueError(f"Unsupported image format: {suffix}")

    prompt = """
You are a precise academic document classification system.

Look carefully at the provided document image and classify it into EXACTLY ONE
of the following categories:

1. "10th_marksheet"
   - Class 10 / Secondary / High School marksheet or certificate
   - Usually contains subjects and marks for class 10

2. "12th_marksheet"
   - Class 12 / Senior Secondary / Intermediate marksheet or certificate
   - Usually contains subjects and marks for class 12

3. "college_marksheet"
   - University / college / undergraduate / postgraduate marksheet
   - May contain semester, course, branch, subject codes, SGPA, CGPA, credits,
     internal/external marks, etc.

4. "unknown"
   - If the document is not clearly one of the above
   - If the image is too unclear to determine the type

Use ONLY information visibly present in the document.

Do not classify based on the filename.

Return ONLY valid JSON in exactly this format:

{
    "document_type": "10th_marksheet"
}

The value of "document_type" MUST be exactly one of:
"10th_marksheet",
"12th_marksheet",
"college_marksheet",
"unknown"
"""

    # response = open_client.chat.completions.create(
    #     model=OPEN_MODEL,
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise document classification system. "
                    "Classify documents only from visible information. "
                    "Never guess."
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": (
                                f"data:{mime_type};base64,"
                                f"{encoded_image}"
                            )
                        },
                    },
                ],
            },
        ],
        response_format={
            "type": "json_object"
        },
        reasoning_effort='low',
        temperature=0,
        max_tokens=150
    )

    content = response.choices[0].message.content

    if not content:
        return "unknown"

    try:
        result = json.loads(content)
        document_type = result.get("document_type", "unknown")

        allowed_types = {
            "10th_marksheet",
            "12th_marksheet",
            "college_marksheet",
            "unknown",
        }

        if document_type not in allowed_types:
            return "unknown"

        return document_type

    except (json.JSONDecodeError, TypeError):
        return "unknown"