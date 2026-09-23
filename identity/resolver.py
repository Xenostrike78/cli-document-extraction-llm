"""
Identity Resolution.

Decides whether records extracted from different documents (and the
candidate's self-reported form) belong to the same person. Name
similarity alone is never trusted -- it is corroborated with DOB,
roll number, and father's name wherever those are present.
"""

import os
import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from identity.name_matcher import compare_names

# Borderline band: name score falls here -> corroborating fields decide;
# if still ambiguous, escalate to LLM adjudication (optional, best-effort).
BORDERLINE_LOW = 0.60
BORDERLINE_HIGH = 0.90


def _normalize_id(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"[\s\-/]", "", str(value)).strip().lower()


def _dob_match(dob1: Optional[str], dob2: Optional[str]) -> Optional[bool]:
    if not dob1 or not dob2:
        return None
    digits1 = re.sub(r"\D", "", dob1)
    digits2 = re.sub(r"\D", "", dob2)
    if not digits1 or not digits2:
        return None
    # Compare as sorted digit sets to tolerate DD-MM-YYYY vs YYYY-MM-DD swaps.
    return sorted(digits1) == sorted(digits2) or digits1 == digits2


@dataclass
class IdentityResolutionResult:
    doc_a: str
    doc_b: str
    name_score: float
    name_decision: str
    dob_match: Optional[bool]
    roll_match: Optional[bool]
    father_name_score: Optional[float]
    final_decision: str  # RESOLVED_SAME | RESOLVED_VARIANT | MISMATCH | NEEDS_REVIEW
    confidence: float
    reasons: List[str] = field(default_factory=list)


def resolve_pair(doc_a: str, record_a: dict, doc_b: str, record_b: dict) -> IdentityResolutionResult:
    name_result = compare_names(record_a.get("name"), record_b.get("name"))
    dob_ok = _dob_match(record_a.get("dob"), record_b.get("dob"))
    roll_a, roll_b = _normalize_id(record_a.get("roll_no")), _normalize_id(record_b.get("roll_no"))
    roll_ok = (roll_a == roll_b) if (roll_a and roll_b) else None

    father_score = None
    if record_a.get("father_name") and record_b.get("father_name"):
        father_score = compare_names(record_a["father_name"], record_b["father_name"]).overall_score

    reasons = list(name_result.reasons)
    corroborating_hits = sum(1 for x in (dob_ok, roll_ok) if x is True)
    corroborating_misses = sum(1 for x in (dob_ok, roll_ok) if x is False)

    # Decision logic: name score is the primary signal; DOB/roll are hard
    # corroboration (a mismatch there overrides an otherwise strong name score,
    # since two different candidates can share a common name).
    if corroborating_misses > 0 and name_result.overall_score < BORDERLINE_HIGH:
        final_decision = "MISMATCH"
        confidence = 0.9
        reasons.append("DOB or roll number conflict outweighs name similarity")
    elif name_result.overall_score >= BORDERLINE_HIGH:
        final_decision = "RESOLVED_SAME" if name_result.decision == "STRONG_MATCH" and name_result.overall_score == 1.0 else "RESOLVED_VARIANT"
        confidence = min(1.0, name_result.overall_score + 0.05 * corroborating_hits)
    elif name_result.overall_score >= BORDERLINE_LOW:
        if corroborating_hits > 0:
            final_decision = "RESOLVED_VARIANT"
            confidence = 0.75 + 0.1 * corroborating_hits
            reasons.append("Name variant resolved via DOB/roll corroboration")
        else:
            final_decision = "NEEDS_REVIEW"
            confidence = name_result.overall_score
            reasons.append("Borderline name similarity with no corroborating field available")
    else:
        final_decision = "MISMATCH"
        confidence = 1 - name_result.overall_score

    return IdentityResolutionResult(
        doc_a=doc_a, doc_b=doc_b,
        name_score=name_result.overall_score, name_decision=name_result.decision,
        dob_match=dob_ok, roll_match=roll_ok, father_name_score=father_score,
        final_decision=final_decision, confidence=round(min(confidence, 1.0), 4),
        reasons=reasons,
    )


def llm_adjudicate(record_a: dict, record_b: dict) -> Optional[str]:
    """
    Best-effort LLM fallback for NEEDS_REVIEW cases only. Uses the same
    Groq client/key already configured for vision extraction. Returns
    'SAME', 'DIFFERENT', or None if the call fails / key is unavailable.
    """
    try:
        from groq import Groq
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return None
        client = Groq(api_key=api_key)
        prompt = (
            "Given these two extracted records, decide if they describe the same person. "
            "Answer with exactly one word: SAME or DIFFERENT.\n\n"
            f"Record A: {json.dumps(record_a)}\n"
            f"Record B: {json.dumps(record_b)}"
        )
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        answer = response.choices[0].message.content.strip().upper()
        if "SAME" in answer:
            return "SAME"
        if "DIFFERENT" in answer:
            return "DIFFERENT"
        return None
    except Exception:
        return None


def resolve_candidate_identity(records: Dict[str, dict]) -> List[IdentityResolutionResult]:
    """
    records: {doc_label: extracted_record_dict}, e.g.
        {"10th_marksheet": {...}, "12th_marksheet": {...}, "self_reported": {...}}
    Returns pairwise resolution results across all documents for one candidate.
    """
    labels = list(records.keys())
    results = []
    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            a, b = labels[i], labels[j]
            result = resolve_pair(a, records[a], b, records[b])
            if result.final_decision == "NEEDS_REVIEW":
                verdict = llm_adjudicate(records[a], records[b])
                if verdict == "SAME":
                    result.final_decision = "RESOLVED_VARIANT"
                    result.reasons.append("LLM adjudication: same person")
                elif verdict == "DIFFERENT":
                    result.final_decision = "MISMATCH"
                    result.reasons.append("LLM adjudication: different person")
                else:
                    result.reasons.append("LLM adjudication unavailable -- flagged for human review")
            results.append(result)
    return results
