# identity/name_rag.py
# TF-IDF based semantic lookup for Indian name variants.
# Falls back to this when the flat ALIASES dictionary in indian_names_kb.py doesn't have the token.
# Uses character n-grams (2-4 chars) which works really well for name spelling variants.

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from identity.indian_names_kb import NAME_VARIANT_KB


class NameRAG:
    def __init__(self):
        self.kb = NAME_VARIANT_KB
        self.vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 4))

        # Build one document per KB group: canonical + all variants concatenated
        docs = [f"{g['canonical']} {' '.join(g['variants'])}" for g in self.kb]
        self.tfidf_matrix = self.vectorizer.fit_transform(docs)

    def lookup_variant(self, token: str, top_k: int = 1):
        """
        Find the closest canonical name for a given token.
        Returns (canonical, distance) where distance=0 is perfect and distance=1 is no match.
        Returns (None, 1.0) if nothing is close enough.
        """
        if not token or not token.strip():
            return None, 1.0

        try:
            query_vec = self.vectorizer.transform([token.lower()])
            sims = cosine_similarity(query_vec, self.tfidf_matrix)[0]
            best_idx = sims.argmax()
            distance = 1.0 - sims[best_idx]

            if distance < 0.60:
                return self.kb[best_idx]["canonical"], distance

        except Exception as e:
            print(f"NameRAG lookup failed for '{token}': {e}")

        return None, 1.0


# Singleton — built once at first call, reused afterwards
_rag_instance = None

def get_name_rag():
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = NameRAG()
    return _rag_instance
