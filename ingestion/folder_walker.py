import json
from pathlib import Path

SUPPORTED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".docx"}
SELF_REPORTED_FILENAME = "self_reported.json"


def load_self_reported(candidate_folder: Path):
    """
    Reads NIC/<candidate_id>/self_reported.json if present -- the
    candidate's own declared data, compared against AI-extracted values.
    Returns {} if the file is absent or malformed (treated as MISSING
    downstream, not a crash).
    """
    form_path = Path(candidate_folder) / SELF_REPORTED_FILENAME
    if not form_path.exists():
        return {}
    try:
        with open(form_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def walk_candidates(root_folder):
    root = Path(root_folder)
    candidates = []
    if not root.exists():
        return candidates
    for candidate_folder in root.iterdir():
        if not candidate_folder.is_dir():
            continue
        files = []
        for file_path in candidate_folder.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                files.append({"name": file_path.name, "path": str(file_path)})
        candidates.append({
            "candidate_id": candidate_folder.name,
            "files": files,
            "self_reported": load_self_reported(candidate_folder),
        })
    return candidates
