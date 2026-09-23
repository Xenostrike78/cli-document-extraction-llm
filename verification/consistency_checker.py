"""
Cross-Document Consistency Check.

Compares each relevant field across all documents belonging to a
candidate (including the self-reported form) and assigns one status:
MATCH, MISMATCH, MISSING, LOW_CONFIDENCE, RESOLVED_VARIANT.

Name fields are judged using the identity resolver's pairwise results
(so a name variant correctly becomes RESOLVED_VARIANT, not MISMATCH).
Numeric fields (percentage, annual_income) allow a small tolerance
since derived values can carry rounding differences.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from identity.resolver import IdentityResolutionResult

NUMERIC_TOLERANCE = {
    "percentage": 0.5,   # percentage points
    "annual_income": 1000,  # currency units
}

EXACT_FIELDS = ["dob", "roll_no"]
NUMERIC_FIELDS = ["percentage", "annual_income"]


@dataclass
class FieldConsistency:
    field_name: str
    values_by_doc: Dict[str, Optional[object]]
    status: str
    notes: List[str] = field(default_factory=list)


def _normalize_id(value):
    if value is None:
        return None
    return str(value).strip().lower().replace(" ", "").replace("-", "")


def check_exact_field(field_name: str, values_by_doc: Dict[str, Optional[str]]) -> FieldConsistency:
    present = {doc: v for doc, v in values_by_doc.items() if v not in (None, "")}
    if not present:
        return FieldConsistency(field_name, values_by_doc, "MISSING", ["Not present in any document"])
    normalized = {_normalize_id(v) for v in present.values()}
    if len(normalized) == 1:
        status = "MATCH" if len(present) == len(values_by_doc) else "MISSING"
        notes = [] if status == "MATCH" else [f"Missing in: {', '.join(d for d in values_by_doc if d not in present)}"]
        return FieldConsistency(field_name, values_by_doc, status, notes)
    return FieldConsistency(field_name, values_by_doc, "MISMATCH", [f"Conflicting values: {present}"])


def check_numeric_field(field_name: str, values_by_doc: Dict[str, Optional[float]]) -> FieldConsistency:
    present = {doc: v for doc, v in values_by_doc.items() if v is not None}
    if not present:
        return FieldConsistency(field_name, values_by_doc, "MISSING", ["Not present in any document"])
    vals = list(present.values())
    tolerance = NUMERIC_TOLERANCE.get(field_name, 0)
    if max(vals) - min(vals) <= tolerance:
        status = "MATCH" if len(present) == len(values_by_doc) else "MISSING"
        notes = [] if status == "MATCH" else [f"Missing in: {', '.join(d for d in values_by_doc if d not in present)}"]
        return FieldConsistency(field_name, values_by_doc, status, notes)
    return FieldConsistency(field_name, values_by_doc, "MISMATCH", [f"Values differ beyond tolerance ({tolerance}): {present}"])


def check_name_field(values_by_doc: Dict[str, Optional[str]],
                      identity_results: List[IdentityResolutionResult]) -> FieldConsistency:
    present = {doc: v for doc, v in values_by_doc.items() if v}
    if not present:
        return FieldConsistency("name", values_by_doc, "MISSING", ["Name not present in any document"])

    decisions = {r.final_decision for r in identity_results}
    if "MISMATCH" in decisions:
        conflicting = [(r.doc_a, r.doc_b) for r in identity_results if r.final_decision == "MISMATCH"]
        return FieldConsistency("name", values_by_doc, "MISMATCH", [f"Name conflict between: {conflicting}"])
    if "NEEDS_REVIEW" in decisions:
        return FieldConsistency("name", values_by_doc, "LOW_CONFIDENCE",
                                 ["One or more document pairs could not be confidently resolved -- needs human review"])
    if any(r.final_decision == "RESOLVED_VARIANT" for r in identity_results):
        return FieldConsistency("name", values_by_doc, "RESOLVED_VARIANT",
                                 ["Naming variation across documents resolved to the same individual"])
    return FieldConsistency("name", values_by_doc, "MATCH", [])


def run_consistency_check(records: Dict[str, dict],
                           identity_results: List[IdentityResolutionResult]) -> List[FieldConsistency]:
    """
    records: {doc_label: extracted_and_derived_record_dict}
    Returns one FieldConsistency per tracked field.
    """
    results = []
    results.append(check_name_field({doc: r.get("name") for doc, r in records.items()}, identity_results))

    for f in EXACT_FIELDS:
        results.append(check_exact_field(f, {doc: r.get(f) for doc, r in records.items()}))

    for f in NUMERIC_FIELDS:
        results.append(check_numeric_field(f, {doc: r.get(f) for doc, r in records.items()}))

    return results
