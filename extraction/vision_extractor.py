import os
import json
import time
import base64
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq, RateLimitError, BadRequestError

from .prompt import build_extraction_prompt, expand_compact, get_schema

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env file.")

client = Groq(api_key=api_key)
MODEL = "qwen/qwen3.8-27b"

# Groq free tier (on_demand): 1000 output tokens/minute, so keep this below 1000.
# On Dev Tier raise it (e.g. 4096) and set LEAN_OUTPUT = False in prompt.py.
MAX_OUTPUT_TOKENS = 900
RATE_LIMIT_RETRIES = 3

# Free tier: a college marksheet does not fit in one 900-token reply, so it is extracted
# in two calls (header, then marks). The pause lets the per-minute output budget reset.
# Set SPLIT_COLLEGE = False (and raise MAX_OUTPUT_TOKENS) on Dev Tier.
SPLIT_COLLEGE = True
SPLIT_PAUSE_SECONDS = 60


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def get_image_mime_type(image_path):
    suffix = Path(image_path).suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".png":
        return "image/png"
    raise ValueError(f"Unsupported image type: {suffix}")


def _create_with_retry(**kwargs):
    """Retry per-minute rate limits; fail fast on errors that waiting cannot fix."""
    for attempt in range(RATE_LIMIT_RETRIES + 1):
        try:
            return client.chat.completions.create(**kwargs)
        except RateLimitError as exc:
            message = str(exc)
            if "Request too large" in message:
                raise RuntimeError(
                    "Request exceeds the per-minute output limit; lower MAX_OUTPUT_TOKENS."
                ) from exc
            if "tokens per day" in message or "(TPD)" in message:
                raise RuntimeError(
                    "Daily token limit reached; wait for the reset or upgrade the Groq tier."
                ) from exc
            if attempt == RATE_LIMIT_RETRIES:
                raise
            try:
                wait = float(exc.response.headers.get("retry-after", 0))
            except (AttributeError, TypeError, ValueError):
                wait = 0
            wait = wait if wait > 0 else 20 * (attempt + 1)
            print(f"    Rate limited; retrying in {wait:.0f}s...")
            time.sleep(wait)


def _call_model(prompt, encoded_image, mime_type, label):
    response = _create_with_retry(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise document extraction system. "
                    "Extract only information explicitly visible "
                    "in the document. Never guess or infer."
                ),
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{encoded_image}"},
                    },
                ],
            },
        ],
        response_format={"type": "json_object"},
        reasoning_effort="none",
        reasoning_format="hidden",
        temperature=0,
        max_tokens=MAX_OUTPUT_TOKENS,
    )

    choice = response.choices[0]
    usage = getattr(response, "usage", None)
    print(
        f"    [{label}] finish_reason={choice.finish_reason}, "
        f"completion_tokens={getattr(usage, 'completion_tokens', '?')}"
    )
    if choice.finish_reason == "length":
        raise RuntimeError(f"Output truncated at {MAX_OUTPUT_TOKENS} tokens ({label}).")

    content = choice.message.content
    if not content:
        raise RuntimeError("Model returned empty response.")
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Model returned invalid JSON ({label}): {exc}")


def extract_from_image(image_path, document_type):
    encoded_image = encode_image(image_path)
    mime_type = get_image_mime_type(image_path)
    schema_class = get_schema(document_type)

    try:
        if document_type == "college_marksheet" and SPLIT_COLLEGE:
            header = _call_model(
                build_extraction_prompt(document_type, part="header"),
                encoded_image, mime_type, "header",
            )
            print(f"    Waiting {SPLIT_PAUSE_SECONDS}s for the output-token budget to reset...")
            time.sleep(SPLIT_PAUSE_SECONDS)
            marks_part = _call_model(
                build_extraction_prompt(document_type, part="marks"),
                encoded_image, mime_type, "marks",
            )
            data = dict(header)
            data["marks"] = marks_part.get("marks") or {}
        else:
            data = _call_model(
                build_extraction_prompt(document_type),
                encoded_image, mime_type, "full",
            )
    except BadRequestError as exc:
        if "max completion tokens" in str(exc):
            raise RuntimeError(
                f"Output truncated at {MAX_OUTPUT_TOKENS} tokens; "
                "use a higher Groq tier or split the extraction further."
            ) from exc
        raise

    full = expand_compact(data, document_type)
    if document_type == "college_marksheet":
        print(
            f"    Extracted result values: "
            f"CGPA={full.get('cgpa')}, "
            f"SGPA={full.get('sgpa')}, "
            f"Percentage={full.get('percentage')}"
        )
    validated = schema_class(**full)

    print("DOCUMENT DATA EXTRACTING DONE..")
    return validated.model_dump()