import re
from pathlib import Path

DOCUMENT_PATTERNS = {
    "10th_marksheet": [
        r"\b10(th)?\b", r"\bclass[-_ ]?10\b", r"\bmatric\b",
        r"\bsecondary\b", r"\bhigh[-_ ]?school\b"
    ],
    "12th_marksheet": [
        r"\b12(th)?\b", r"\bclass[-_ ]?12\b", r"\bintermediate\b",
        r"\bhigher[-_ ]?secondary\b"
    ],
    "college_marksheet": [
        r"\bcollege\b", r"\buniversity\b", r"\bdegree\b",
        r"\bgraduation\b", r"\bsemester\b", r"\bsem[-_ ]?\d+\b",
        r"\bbtech\b", r"\bmtech\b", r"\bbca\b", r"\bmca\b"
    ]
}

def classify_by_filename(file_path):
    name = Path(file_path).stem.lower().replace("-", " ").replace("_", " ")
    for doc_type, patterns in DOCUMENT_PATTERNS.items():
        if any(re.search(pattern, name, re.IGNORECASE) for pattern in patterns):
            return doc_type
    return "unknown"

def classify_document(file_path):
    return classify_by_filename(file_path)
