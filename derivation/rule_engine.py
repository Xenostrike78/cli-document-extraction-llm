"""
Derived Field Computation.

Reads config/rules.json and computes target fields (e.g. annual_income,
percentage) from whichever source fields a given record actually has.
Rules are data, not code -- add a new derived field by editing the JSON,
no changes needed here.
"""

import json
from pathlib import Path
from typing import Optional

RULES_PATH = Path(__file__).resolve().parent.parent / "config" / "rules.json"


def load_rules() -> dict:
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _prefer_first_present_else_multiply(record: dict, sources: list, multiply_by: float):
    primary, fallback = sources[0], sources[1]
    if record.get(primary) is not None:
        return record[primary], f"taken directly from '{primary}'"
    if record.get(fallback) is not None:
        value = round(float(record[fallback]) * multiply_by, 2)
        return value, f"derived: {fallback} ({record[fallback]}) x {multiply_by}"
    return None, "no source field available"


RULE_HANDLERS = {
    "prefer_first_present_else_multiply": _prefer_first_present_else_multiply,
}


def compute_derived_fields(record: dict, rules: Optional[dict] = None) -> dict:
    """
    record: an extracted document record (dict).
    Returns {field_name: {"value": ..., "explanation": ...}} for every
    target field defined in rules.json.
    """
    rules = rules or load_rules()
    derived = {}
    for field_name, spec in rules.items():
        handler = RULE_HANDLERS.get(spec["rule"])
        if not handler:
            derived[field_name] = {"value": None, "explanation": f"unknown rule '{spec['rule']}'"}
            continue
        value, explanation = handler(record, spec["sources"], spec.get("multiply_by", 1))
        derived[field_name] = {"value": value, "explanation": explanation}
    return derived
