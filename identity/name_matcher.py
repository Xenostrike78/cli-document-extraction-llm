# identity/name_matcher.py
# Normalizes names and scores how similar two names are.
# Used by resolver.py as one signal among several — it doesn't make the final call alone.

import re
import unicodedata
from dataclasses import dataclass
from typing import List

from rapidfuzz.fuzz import ratio, WRatio
from unidecode import unidecode

from identity.indian_names_kb import FLAT_ALIASES as ALIASES
from identity.name_rag import get_name_rag

# Common titles that shouldn't be treated as part of the name
TITLES = {"mr", "mrs", "ms", "miss", "dr", "prof", "sir", "shri", "smt"}

@dataclass
class Token:
    value: str
    token_type: str  # "initial" | "title" | "full"


@dataclass
class NormalizedName:
    original: str
    canonical_tokens: List[str]
    canonical_name: str


@dataclass
class NameMatchResult:
    name1: str
    name2: str
    overall_score: float
    decision: str   # STRONG_MATCH | POSSIBLE_MATCH | LOW_SIMILARITY
    reasons: List[str]


def _clean(text):
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _is_initial(token):
    return len(token) == 1 and token.isalpha()


def normalize_name(name: str) -> NormalizedName:
    """
    Converts a raw name string into a canonical form that can be compared
    across documents. Handles:
      - Unicode/transliteration (unidecode)
      - Titles (Mr, Dr, Shri...)
      - Name abbreviations (Md -> Mohammad via ALIASES KB)
      - Rare variants via TF-IDF RAG fallback
    """
    if not name:
        return NormalizedName(original=name or "", canonical_tokens=[], canonical_name="")

    text = _clean(unidecode(name.strip().lower()))
    raw_tokens = text.split()
    tokens = [Token(t, "initial" if _is_initial(t) else ("title" if t in TITLES else "full")) for t in raw_tokens]
    tokens = [t for t in tokens if t.token_type != "title"]

    rag = get_name_rag()
    canonical_tokens = []

    for t in tokens:
        if t.token_type == "initial":
            canonical_tokens.append(t.value)
        else:
            # Try flat dictionary first (fast, deterministic)
            canon = ALIASES.get(t.value)

            # Fall back to TF-IDF RAG for anything not in the dictionary
            if not canon:
                rag_canon, dist = rag.lookup_variant(t.value)
                if rag_canon and dist < 1.0:
                    canon = rag_canon

            canonical_tokens.append(canon if canon else t.value)

    return NormalizedName(
        original=name,
        canonical_tokens=canonical_tokens,
        canonical_name=" ".join(canonical_tokens),
    )


def _token_similarity(n1: NormalizedName, n2: NormalizedName) -> float:
    s1, s2 = set(n1.canonical_tokens), set(n2.canonical_tokens)
    if not s1 or not s2:
        return 0.0
    return len(s1 & s2) / len(s1 | s2)


def _initial_compatibility(t1: List[str], t2: List[str]) -> float:
    """Check if initials are compatible with full tokens (e.g. 'A' matches 'Ahmad')."""
    if not t1 or not t2:
        return 0.0
    matched = comparisons = 0
    for a, b in zip(t1, t2):
        comparisons += 1
        if a == b:
            matched += 1
        elif _is_initial(a) and a[0] == b[0]:
            matched += 1
        elif _is_initial(b) and b[0] == a[0]:
            matched += 1
    return matched / comparisons if comparisons else 0.0


def _order_similarity(n1: NormalizedName, n2: NormalizedName) -> float:
    t1, t2 = n1.canonical_tokens, n2.canonical_tokens
    if not t1 or not t2:
        return 0.0
    if t1 == t2:
        return 1.0
    if set(t1) == set(t2):
        return 0.8   # same tokens, different order (common in Indian names)
    return ratio(" ".join(t1), " ".join(t2)) / 100.0


def compare_names(raw_name1: str, raw_name2: str) -> NameMatchResult:
    """Score the similarity between two raw name strings (0.0 to 1.0)."""
    if not raw_name1 or not raw_name2:
        return NameMatchResult(raw_name1, raw_name2, 0.0, "LOW_SIMILARITY", ["One or both names missing"])

    n1 = normalize_name(raw_name1)
    n2 = normalize_name(raw_name2)

    if n1.canonical_name == n2.canonical_name:
        return NameMatchResult(raw_name1, raw_name2, 1.0, "STRONG_MATCH", ["Exact canonical name match"])

    token_score   = _token_similarity(n1, n2)
    initial_score = _initial_compatibility(n1.canonical_tokens, n2.canonical_tokens)
    fuzzy_score   = WRatio(n1.canonical_name, n2.canonical_name) / 100.0
    order_score   = _order_similarity(n1, n2)

    overall = 0.30 * token_score + 0.25 * initial_score + 0.30 * fuzzy_score + 0.15 * order_score

    reasons = []
    if token_score   >= 0.8: reasons.append("High token overlap")
    if initial_score >= 0.8: reasons.append("Initial/full-name compatibility")
    if fuzzy_score   >= 0.85: reasons.append("High fuzzy similarity")
    if order_score   >= 0.8: reasons.append("Compatible token order")
    if any(alias in raw_name1.lower() or alias in raw_name2.lower() for alias in ALIASES):
        reasons.append("Possible abbreviation/alias variation")

    decision = "STRONG_MATCH" if overall >= 0.90 else "POSSIBLE_MATCH" if overall >= 0.75 else "LOW_SIMILARITY"
    return NameMatchResult(raw_name1, raw_name2, round(overall, 4), decision, reasons)
