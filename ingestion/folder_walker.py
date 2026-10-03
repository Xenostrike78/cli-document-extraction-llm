import json
from pathlib import Path

SUPPORTED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".docx"}


def walk_candidates(root_folder):
    root = Path(root_folder)
    candidates = []
    if not root.exists() or not root.is_dir():
        return candidates
    for candidate_folder in root.iterdir():
        if not candidate_folder.is_dir():
            continue
        files = []
        for file_path in sorted(candidate_folder.rglob("*")):
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                files.append({"path": str(file_path)})
        candidates.append({
            "candidate_id": candidate_folder.name,
            "files": files,
        })
    return candidates
