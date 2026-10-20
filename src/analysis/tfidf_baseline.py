"""
Interpretable TF-IDF baseline for cricket text similarity and topic representation.
Preserves cricket numbers, overs (19.4), and scores (182/5, 82*).
"""

from typing import List, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine_similarity


# Custom token pattern capturing scores (82*), overs (19.4), scoreboards (182/5), and words
CRICKET_TOKEN_PATTERN = r"(?u)\b\d{1,3}\*(?!\w)|\b\d{1,2}\.\d\b|\b\d{1,3}/\d{1,2}\b|\b\w+\b"


class CricketTfidfBaseline:
    """
    Sparse TF-IDF baseline model for measuring lexical overlap and comparing against dense embeddings.
    """

    def __init__(
        self,
        mode: str = "word",
        ngram_range: Tuple[int, int] = (1, 2),
        min_df: int = 1,
        max_features: Optional[int] = 5000,
    ):
        """
        Args:
            mode: 'word' for word n-grams or 'char_wb' for sub-word character n-grams within word boundaries.
            ngram_range: n-gram range tuple.
            min_df: Minimum document frequency.
            max_features: Maximum vocabulary size.
        """
        self.mode = mode
        self.ngram_range = ngram_range
        self.min_df = min_df
        self.max_features = max_features

        if mode == "word":
            self.vectorizer = TfidfVectorizer(
                token_pattern=CRICKET_TOKEN_PATTERN,
                ngram_range=ngram_range,
                min_df=min_df,
                max_features=max_features,
                lowercase=True,
                norm="l2",
            )
        elif mode == "char_wb":
            self.vectorizer = TfidfVectorizer(
                analyzer="char_wb",
                ngram_range=ngram_range,
                min_df=min_df,
                max_features=max_features,
                lowercase=True,
                norm="l2",
            )
        else:
            raise ValueError(f"Unsupported TF-IDF mode: {mode}")

        self.is_fitted = False

    def fit(self, documents: List[str]) -> "CricketTfidfBaseline":
        """Fits vocabulary on a corpus of cricket documents."""
        sanitized = [d.strip() if d else "empty_token" for d in documents]
        self.vectorizer.fit(sanitized)
        self.is_fitted = True
        return self

    def transform(self, documents: List[str]) -> np.ndarray:
        """Transforms documents to sparse TF-IDF array."""
        if not self.is_fitted:
            raise RuntimeError("CricketTfidfBaseline must be fitted before transforming.")
        sanitized = [d.strip() if d else "empty_token" for d in documents]
        sparse_mat = self.vectorizer.transform(sanitized)
        return sparse_mat.toarray()

    def fit_transform(self, documents: List[str]) -> np.ndarray:
        """Fits and transforms documents in a single pass."""
        return self.fit(documents).transform(documents)

    def compute_similarity(self, docs_a: List[str], docs_b: List[str]) -> np.ndarray:
        """Computes pairwise cosine similarity between two sets of documents."""
        if not self.is_fitted:
            # Fit on the combined corpus if not fitted yet
            self.fit(docs_a + docs_b)

        vecs_a = self.transform(docs_a)
        vecs_b = self.transform(docs_b)
        return sklearn_cosine_similarity(vecs_a, vecs_b)

    def get_top_features_for_doc(self, doc: str, top_n: int = 5) -> List[Tuple[str, float]]:
        """Returns the highest-weighted TF-IDF terms in a given document."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted to extract features.")
        vec = self.transform([doc])[0]
        feature_names = self.vectorizer.get_feature_names_out()

        non_zero_idx = np.where(vec > 0.0)[0]
        if len(non_zero_idx) == 0:
            return []

        sorted_idx = non_zero_idx[np.argsort(-vec[non_zero_idx])][:top_n]
        return [(str(feature_names[i]), float(vec[i])) for i in sorted_idx]
