# identity/resolver.py
# Figures out whether documents in a candidate's folder belong to the same person.
# Logic: compare hard fields first (DOB, parent names), then check names last.

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from identity.name_matcher import compare_names


def _normalize_id(value):
    if not value:
        return ""
    return re.sub(r"[\s\-/]", "", str(value)).strip().lower()


def _dob_match(dob1, dob2):
    """Compare two DOBs ignoring separator format (dd-mm-yyyy vs ddmmyyyy etc)."""
    if not dob1 or not dob2:
        return None
    d1 = re.sub(r"\D", "", dob1)
    d2 = re.sub(r"\D", "", dob2)
    if not d1 or not d2:
        return None
    # sorted() handles cases where day/month are in different order
    return sorted(d1) == sorted(d2) or d1 == d2


@dataclass
class IdentityResolutionResult:
    doc_a: str
    doc_b: str
    name_score: float
    name_decision: str
    dob_match: Optional[bool]
    roll_match: Optional[bool]   # kept for report compatibility, always None now
    father_name_score: Optional[float]
    mother_name_score: Optional[float]
    final_decision: str
    confidence: float
    reasons: List[str] = field(default_factory=list)
    matched_fields: List[str] = field(default_factory=list)
    contradictions: List[str] = field(default_factory=list)
    unavailable_fields: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def _get(record, key):
    val = record.get(key)
    return val if val else None


def _compare_field(val_a, val_b, exact=True, fuzzy_threshold=0.85):
    """Return MATCH / MISMATCH / NOT_COMPARABLE for a pair of field values."""
    if not val_a or not val_b:
        return "NOT_COMPARABLE"
    if exact:
        return "MATCH" if _normalize_id(val_a) == _normalize_id(val_b) else "MISMATCH"
    score = compare_names(str(val_a), str(val_b)).overall_score
    return "MATCH" if score >= fuzzy_threshold else "MISMATCH"


def resolve_pair(doc_a, record_a, doc_b, record_b):
    """
    Compare two document records and decide if they belong to the same person.

    Step 1: Extract the fields we care about.
    Step 2: Compare non-name fields (DOB, parents, gender, school).
    Step 3: Draw an initial conclusion from those fields alone.
    Step 4: Run name matching as the final check to confirm or challenge that conclusion.
    """

    # --- Step 1: pull out the fields ---
    dob_a,    dob_b    = _get(record_a, "dob"),          _get(record_b, "dob")
    father_a, father_b = _get(record_a, "father_name"),  _get(record_b, "father_name")
    mother_a, mother_b = _get(record_a, "mother_name"),  _get(record_b, "mother_name")
    gender_a, gender_b = _get(record_a, "gender"),       _get(record_b, "gender")
    school_a, school_b = _get(record_a, "school"),       _get(record_b, "school")
    year_a,   year_b   = _get(record_a, "passing_year"), _get(record_b, "passing_year")

    # --- Step 2: compare ---
    dob_comp    = "MATCH" if _dob_match(dob_a, dob_b) else ("NOT_COMPARABLE" if not dob_a or not dob_b else "MISMATCH")
    father_comp = _compare_field(father_a, father_b, exact=False, fuzzy_threshold=0.80)
    mother_comp = _compare_field(mother_a, mother_b, exact=False, fuzzy_threshold=0.80)
    gender_comp = _compare_field(gender_a, gender_b, exact=True)
    school_comp = _compare_field(school_a, school_b, exact=False, fuzzy_threshold=0.85)

    matched, contradictions, unavailable, warnings = [], [], [], []

    for fname, comp, va, vb in [
        ("dob",         dob_comp,    dob_a,    dob_b),
        ("father_name", father_comp, father_a, father_b),
        ("mother_name", mother_comp, mother_a, mother_b),
    ]:
        if comp == "MATCH":
            matched.append(fname)
        elif comp == "MISMATCH":
            contradictions.append(fname)
        elif not va or not vb:
            unavailable.append(f"{fname}_missing")

    # Flag suspicious academic timelines (10th to 12th in under a year)
    if year_a and year_b and str(year_a).isdigit() and str(year_b).isdigit():
        diff = abs(int(year_a) - int(year_b))
        is_cross_level = (
            ("10th" in doc_a.lower() and "12th" in doc_b.lower()) or
            ("10th" in doc_b.lower() and "12th" in doc_a.lower())
        )
        if is_cross_level and diff < 1:
            warnings.append("Suspicious academic progression (10th to 12th gap < 1 year)")

    # Gender and school are soft signals — mismatch is a warning, not a contradiction
    if gender_comp == "MATCH":      matched.append("gender")
    elif gender_comp == "MISMATCH": warnings.append("Gender mismatch")

    if school_comp == "MATCH":      matched.append("school")
    elif school_comp == "MISMATCH": warnings.append("Institution changed")

    # --- Step 3: initial verdict from non-name fields ---
    strong_contradictions = [c for c in contradictions if c in ["dob"]]
    parent_contradictions = [c for c in contradictions if c in ["father_name", "mother_name"]]
    strong_corroborations = [m for m in matched if m in ["dob", "father_name", "mother_name"]]

    reasons = []
    if strong_contradictions:
        field_decision, field_confidence = "NON_MATCH", 0.90
        reasons.append(f"Strong contradiction in {strong_contradictions}")
    elif parent_contradictions:
        field_decision, field_confidence = "PROBABLE_NON_MATCH", 0.80
        reasons.append(f"Parent name contradiction: {parent_contradictions}")
    elif len(contradictions) > 1:
        field_decision, field_confidence = "PROBABLE_NON_MATCH", 0.75
        reasons.append(f"Multiple contradictions: {contradictions}")
    elif len(strong_corroborations) >= 2:
        field_decision, field_confidence = "MATCH", 0.85
        reasons.append(f"Strong corroboration from non-name fields: {strong_corroborations}")
    elif len(strong_corroborations) == 1:
        field_decision, field_confidence = "PROBABLE_MATCH", 0.65
        reasons.append(f"Partial corroboration from non-name fields: {strong_corroborations}")
    else:
        field_decision, field_confidence = "NEEDS_REVIEW", 0.50
        reasons.append("Not enough non-name fields to draw a firm conclusion")

    # --- Step 4: name matching as the final check ---
    name_a = _get(record_a, "name")
    name_b = _get(record_b, "name")
    name_result = compare_names(name_a, name_b)

    if name_result.overall_score >= 0.85:
        matched.append("name")
        reasons.append(f"Name match supports identity (score {name_result.overall_score:.2f})")
        if field_decision in ["MATCH", "PROBABLE_MATCH", "NEEDS_REVIEW"]:
            final_decision = "MATCH"
            final_confidence = min(0.99, field_confidence + 0.30)
        else:
            # Name matches but hard fields said no — leave it for a human
            final_decision = "NEEDS_REVIEW"
            final_confidence = 0.60
            reasons.append("Name matches but strong contradictions exist in other fields")

    elif name_a and name_b:
        contradictions.append("name")
        reasons.append(f"Name mismatch (score {name_result.overall_score:.2f})")
        if field_decision == "MATCH":
            final_decision = "NEEDS_REVIEW"
            final_confidence = 0.70
            reasons.append("Strong field corroboration but name mismatches")
        else:
            final_decision = "NON_MATCH" if field_decision in ["NON_MATCH", "PROBABLE_NON_MATCH"] else "PROBABLE_NON_MATCH"
            final_confidence = min(0.99, field_confidence + 0.20)

    else:
        # One or both names missing — fall back to whatever the fields said
        unavailable.append("name")
        final_decision = field_decision
        final_confidence = field_confidence

    return IdentityResolutionResult(
        doc_a=doc_a,
        doc_b=doc_b,
        name_score=name_result.overall_score,
        name_decision=name_result.decision,
        dob_match=True if dob_comp == "MATCH" else (False if dob_comp == "MISMATCH" else None),
        roll_match=None,
        father_name_score=compare_names(father_a, father_b).overall_score if father_a and father_b else None,
        mother_name_score=compare_names(mother_a, mother_b).overall_score if mother_a and mother_b else None,
        final_decision=final_decision,
        confidence=round(min(final_confidence, 1.0), 4),
        reasons=reasons,
        matched_fields=matched,
        contradictions=contradictions,
        unavailable_fields=unavailable,
        warnings=warnings,
    )


def resolve_candidate_identity(records: Dict[str, dict]) -> List[IdentityResolutionResult]:
    """Run pairwise identity resolution across all documents for a candidate."""
    labels = list(records.keys())
    results = []
    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            results.append(resolve_pair(labels[i], records[labels[i]], labels[j], records[labels[j]]))
    return results
