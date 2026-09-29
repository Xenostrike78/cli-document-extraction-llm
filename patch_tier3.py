"""Patch script: replace calculate_subject_wise_percentage in vision_extractor.py"""
from pathlib import Path

path = Path("extraction/vision_extractor.py")
content = path.read_text(encoding="utf-8")

start_marker = "def calculate_subject_wise_percentage(subjects: list):"
next_marker  = "def resolve_percentage("

start_idx = content.index(start_marker)
end_idx   = content.index(next_marker)

new_func = '''\
def calculate_subject_wise_percentage(subjects: list):
    """
    Tier 3 - Subject-wise Marks Aggregation.

    Strategy (in order of preference):
    1. Use max_marks if explicitly provided by the LLM.
    2. Assume 100 marks per subject as a fallback (CBSE/standard default).
       Note: theory_marks and practical_marks on CBSE marksheets are
       *obtained* values, NOT the maximum -- do NOT sum them as the max.

    Only subjects where total_marks (obtained) is non-null are counted.
    Returns float percentage or None if no valid subjects are found.
    """
    total_obtained = 0.0
    total_maximum  = 0.0
    valid_count    = 0

    for subj in subjects:
        obtained = subj.get("total_marks")
        if obtained is None:
            continue
        try:
            o = float(obtained)
        except (TypeError, ValueError):
            continue

        # Strategy 1: explicit max_marks field
        maximum = None
        if subj.get("max_marks") is not None:
            try:
                maximum = float(subj["max_marks"])
            except (TypeError, ValueError):
                maximum = None

        # Strategy 2: assume 100 per subject (CBSE / most board standard)
        if maximum is None:
            maximum = 100.0

        if maximum > 0:
            total_obtained += o
            total_maximum  += maximum
            valid_count    += 1

    if valid_count > 0 and total_maximum > 0:
        return round((total_obtained / total_maximum) * 100, 2)
    return None


'''

patched = content[:start_idx] + new_func + content[end_idx:]
path.write_text(patched, encoding="utf-8")
print("Patch applied.")
print("Total lines:", patched.count("\n"))
