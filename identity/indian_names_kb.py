# identity/indian_names_kb.py
# Lookup tables for common Indian name variants.
#
# Two exports:
#   NAME_VARIANT_KB  - full structured list used by name_rag.py for TF-IDF indexing
#   FLAT_ALIASES     - flat dict built from the KB, used by name_matcher.py for O(1) lookups
#
# To add a new name group, append an entry to NAME_VARIANT_KB.
# FLAT_ALIASES is generated automatically at the bottom of this file.

from .names_variant import NAME_VARIANT_KB




# ─────────────────────────────────────────────────────────────
# Flat alias dict: variant → canonical
# Used by name_matcher.py (Tier-1 deterministic expansion)
# ─────────────────────────────────────────────────────────────
def build_flat_aliases() -> dict:
    out = {}
    for group in NAME_VARIANT_KB:
        canon = group["canonical"]
        for v in group["variants"]:
            key = v.strip().lower()
            if key and key != canon:
                out[key] = canon
    return out


FLAT_ALIASES: dict = build_flat_aliases()
