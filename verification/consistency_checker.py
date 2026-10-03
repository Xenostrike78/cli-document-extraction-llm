"""
Cross-Document Consistency Check.
"""

from typing import Dict, List, Optional

# Name convention knowledge base
from identity.names_variant import NAME_VARIANT_KB


def _normalize_id(value):

    if value is None:
        return None

    return (
        str(value)
        .strip()
        .lower()
        .replace(" ", "")
        .replace("-", "")
    )


def _normalize_name_for_identity(value):

    if not value:
        return None

    val_str = str(value).strip().lower()

    if "/" in val_str:
        val_str = val_str.split("/")[0].strip()

    return (
        val_str
        .replace(" ", "")
        .replace("-", "")
    )


# ============================================================
# NAME CONVENTION / CANONICAL NAME
# ============================================================

def _normalize_name_token(value: str) -> str:
    """
    Normalizes a single name token for variant matching.
    """

    if not value:
        return ""

    return (
        str(value)
        .strip()
        .lower()
        .replace(".", "")
        .replace(",", "")
    )


def _build_name_variant_lookup():
    """
    Creates:

        variant -> canonical

    from NAME_VARIANT_KB.
    """

    lookup = {}

    for group in NAME_VARIANT_KB:

        canonical = _normalize_name_token(
            group["canonical"]
        )

        if not canonical:
            continue

        # Canonical value maps to itself
        lookup[canonical] = canonical

        for variant in group.get("variants", []):

            normalized_variant = _normalize_name_token(
                variant
            )

            if normalized_variant:
                lookup[normalized_variant] = canonical

    return lookup


NAME_VARIANT_LOOKUP = _build_name_variant_lookup()


def generate_final_name(name: Optional[str]) -> Optional[str]:
    """
    Generates the canonical name using the name-convention
    knowledge base.

    Original extracted name is NOT modified.

    Example:

        "Mohd. Khan"
            ->
        "mohammad khan"
    """

    if not name:
        return None

    name = str(name).strip()

    if not name:
        return None

    # Normalize separators
    name = name.replace(",", " ")

    # Remove duplicate whitespace
    name = " ".join(name.split())

    tokens = name.split()

    canonical_tokens = []

    for token in tokens:

        normalized_token = _normalize_name_token(token)

        if not normalized_token:
            continue

        canonical = NAME_VARIANT_LOOKUP.get(
            normalized_token
        )

        if canonical:
            canonical_tokens.append(canonical)
        else:
            # Preserve unknown names
            canonical_tokens.append(
                normalized_token
            )

    if not canonical_tokens:
        return None

    return " ".join(canonical_tokens)


# ============================================================
# IDENTITY CONFIDENCE SCORE
# ============================================================

def evaluate_overall_identity(
    records_dict: Dict[str, list]
) -> float:

    """
    Calculates an identity confidence score using ONLY:

        1. Name
        2. Father's Name
        3. Mother's Name

    Uses canonical name resolution via NAME_VARIANT_KB before
    comparison, so variants like "Mohd" and "Mohammad" are
    treated as the same token.

    Scoring:

        Name          -> 50%
        Father's Name -> 25%
        Mother's Name -> 25%

    Missing fields are ignored and do not reduce the score.
    """

    import difflib

    # ---------------------------------------------------------
    # 1. Flatten all documents
    # ---------------------------------------------------------

    all_docs = []

    for doc_list in records_dict.values():

        if isinstance(doc_list, list):
            all_docs.extend(doc_list)

        else:
            all_docs.append(doc_list)

    if not all_docs:
        return 0.0

    # ---------------------------------------------------------
    # 2. Field weights
    # ---------------------------------------------------------

    FIELD_WEIGHTS = {
        "name": 0.50,
        "father_name": 0.25,
        "mother_name": 0.25,
    }

    # ---------------------------------------------------------
    # 3. Normalize names via canonical resolution
    # ---------------------------------------------------------

    def normalize_name(value):

        if not value:
            return None

        value = str(value).strip().lower()

        if "/" in value:
            value = value.split("/")[0].strip()

        # Strip punctuation
        value = (
            value
            .replace("-", " ")
            .replace(".", "")
            .replace(",", "")
        )

        # Resolve each token to its canonical form
        tokens = value.split()
        canonical_tokens = []

        for token in tokens:
            canonical = NAME_VARIANT_LOOKUP.get(token, token)
            canonical_tokens.append(canonical)

        return " ".join(canonical_tokens).strip()

    # ---------------------------------------------------------
    # 4. Calculate similarity between values
    #    Uses token-set Jaccard similarity so that completely
    #    different names (different word sets) score near 0,
    #    while identical or near-identical names score near 1.
    # ---------------------------------------------------------

    def calculate_similarity(values):

        if not values:
            return None

        if len(values) == 1:
            return 1.0

        scores = []

        for i in range(len(values)):

            for j in range(i + 1, len(values)):

                set_a = set(values[i].split())
                set_b = set(values[j].split())

                intersection = len(set_a & set_b)
                union = len(set_a | set_b)

                score = intersection / union if union else 0.0

                scores.append(score)

        if not scores:
            return 1.0

        return sum(scores) / len(scores)

    # ---------------------------------------------------------
    # 5. Calculate each field score
    # ---------------------------------------------------------

    field_scores = {}

    for field in FIELD_WEIGHTS:

        values = []

        for doc in all_docs:

            value = normalize_name(
                doc.get(field)
            )

            if value:
                values.append(value)

        field_scores[field] = calculate_similarity(
            values
        )

    # ---------------------------------------------------------
    # 6. Weighted scoring
    # ---------------------------------------------------------

    weighted_score = 0.0
    available_weight = 0.0

    for field, weight in FIELD_WEIGHTS.items():

        score = field_scores[field]

        if score is None:
            continue

        weighted_score += score * weight
        available_weight += weight

    if available_weight == 0:
        return 0.0

    final_score = (
        weighted_score /
        available_weight
    )

    return round(
        max(
            0.0,
            min(final_score, 1.0)
        ),
        4
    )


# ============================================================
# PATCH EXISTING JSON FILES
# ============================================================

def patch_existing_jsons():

    """
    Updates existing JSON files in the output/ directory.

    Adds:

        identity_confidence_score

    And for every document:

        final_name

    The original 'name' field is preserved.
    """

    import glob
    import json
    import os

    output_dir = os.path.join(
        os.path.dirname(
            os.path.dirname(__file__)
        ),
        "output"
    )

    search_path = os.path.join(
        output_dir,
        "*.json"
    )

    for f in glob.glob(search_path):

        with open(
            f,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if "documents" in data:

            # -------------------------------------------------
            # 1. Generate final_name for every document
            # -------------------------------------------------

            documents = data["documents"]

            if isinstance(documents, dict):

                for doc_key, doc_data in documents.items():

                    if isinstance(doc_data, list):

                        for record in doc_data:

                            if isinstance(record, dict):

                                original_name = record.get(
                                    "name"
                                )

                                record["final_name"] = (
                                    generate_final_name(
                                        original_name
                                    )
                                )

                    elif isinstance(doc_data, dict):

                        original_name = doc_data.get(
                            "name"
                        )

                        doc_data["final_name"] = (
                            generate_final_name(
                                original_name
                            )
                        )

            # -------------------------------------------------
            # 2. Remove old same_person field
            # -------------------------------------------------

            if "same_person" in data:
                del data["same_person"]

            # -------------------------------------------------
            # 3. Calculate identity confidence
            # -------------------------------------------------

            data["identity_confidence_score"] = (
                evaluate_overall_identity(
                    data["documents"]
                )
            )

            # -------------------------------------------------
            # 4. Save JSON
            # -------------------------------------------------

            with open(
                f,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    data,
                    file,
                    indent=2,
                    ensure_ascii=False
                )

    print("Patching completed.")


if __name__ == "__main__":

    import sys
    import os

    # Add project root to Python path
    sys.path.append(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )
    )

    patch_existing_jsons()
