"""
Model-agnostic embedding interface with explicit test double and opt-in sentence-transformers support.
"""

from __future__ import annotations

import abc
import hashlib
from typing import List, Optional
import numpy as np


class BaseEmbeddingModel(abc.ABC):
    """Abstract base interface for semantic text embedding models."""

    def __init__(self, model_name: str, dimension: int, is_test_double: bool = False):
        self.model_name = model_name
        self.dimension = dimension
        self.is_test_double = is_test_double

    @abc.abstractmethod
    def embed(self, texts: List[str]) -> np.ndarray:
        """
        Generates normalized dense embeddings for a list of texts.
        Returns:
            np.ndarray: Matrix of shape (len(texts), dimension) with float32 values.
        """
        pass

    def validate_matrix(self, matrix: np.ndarray, expected_count: int) -> None:
        """Validates output array dimensions and data type."""
        if not isinstance(matrix, np.ndarray):
            raise TypeError(f"Embedding output must be a numpy ndarray, got {type(matrix)}")
        if matrix.shape != (expected_count, self.dimension):
            raise ValueError(
                f"Embedding matrix shape mismatch: expected ({expected_count}, {self.dimension}), got {matrix.shape}"
            )


class DeterministicTestEmbeddingModel(BaseEmbeddingModel):
    """
    Explicit test double for offline, deterministic unit and integration tests.
    Produces unit-normalized 384-dimensional vectors based on stable token hashing.
    NEVER disguised as a real ML model.
    """

    def __init__(self, dimension: int = 384):
        super().__init__(
            model_name="test-deterministic-hash-384",
            dimension=dimension,
            is_test_double=True,
        )

    def embed(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)

        vectors = []
        for text in texts:
            clean = text.strip() if text else ""
            if not clean:
                # Return zero vector for empty/whitespace text
                vectors.append(np.zeros(self.dimension, dtype=np.float32))
                continue

            import re
            # Extract clean tokens without trailing punctuation
            tokens = re.findall(r"[A-Za-z0-9]+(?:\.[0-9]+)?", clean.lower())
            vec = np.zeros(self.dimension, dtype=np.float32)

            for token in tokens:
                token_hash = int(hashlib.md5(token.encode("utf-8")).hexdigest()[:8], 16)
                idx = token_hash % self.dimension
                sign = 1.0 if (token_hash % 2 == 0) else -1.0
                vec[idx] += sign

            # Add bigram signals for semantic continuity
            for i in range(len(tokens) - 1):
                bigram = f"{tokens[i]}_{tokens[i+1]}"
                bi_hash = int(hashlib.md5(bigram.encode("utf-8")).hexdigest()[:8], 16)
                idx = bi_hash % self.dimension
                sign = 1.0 if (bi_hash % 2 == 0) else -1.0
                vec[idx] += sign * 0.75

            # L2-normalize to unit hypersphere
            norm = np.linalg.norm(vec)
            if norm > 1e-9:
                vec = vec / norm
            else:
                vec[0] = 1.0

            vectors.append(vec)

        matrix = np.array(vectors, dtype=np.float32)
        self.validate_matrix(matrix, len(texts))
        return matrix


class SentenceTransformerEmbeddingModel(BaseEmbeddingModel):
    """
    Local sentence-transformers embedding model (all-MiniLM-L6-v2).
    Requires explicit opt-in and local model cache.
    """

    DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    DEFAULT_DIMENSION = 384

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        dimension: int = DEFAULT_DIMENSION,
        device: str = "cpu",
    ):
        super().__init__(
            model_name=model_name,
            dimension=dimension,
            is_test_double=False,
        )
        self.device = device
        self._model = None

    def _load_model(self) -> None:
        if self._model is not None:
            return

        try:
            from sentence_transformers import SentenceTransformer  # Lazy import
        except ImportError as e:
            raise RuntimeError(
                f"sentence-transformers is not available: {e}. "
                "Use DeterministicTestEmbeddingModel for tests or install sentence-transformers."
            )

        try:
            self._model = SentenceTransformer(self.model_name, device=self.device)
        except Exception as e:
            raise RuntimeError(
                f"Failed to load sentence-transformers model '{self.model_name}': {e}. "
                "Verify model cache or network access."
            )

    def embed(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)

        self._load_model()
        # Handle empty strings gracefully
        sanitized = [t if (t and t.strip()) else " " for t in texts]

        embeddings = self._model.encode(
            sanitized,
            batch_size=32,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        matrix = np.asarray(embeddings, dtype=np.float32)
        # Zero out completely empty text rows
        for i, t in enumerate(texts):
            if not t or not t.strip():
                matrix[i] = np.zeros(self.dimension, dtype=np.float32)

        self.validate_matrix(matrix, len(texts))
        return matrix


def get_embedding_model(model_name: Optional[str] = None) -> BaseEmbeddingModel:
    """Factory creating embedding model according to specification."""
    if not model_name or model_name in ("test", "test-deterministic-hash-384"):
        return DeterministicTestEmbeddingModel()
    elif "MiniLM" in model_name or "sentence-transformers" in model_name:
        return SentenceTransformerEmbeddingModel(model_name=model_name)
    else:
        raise ValueError(f"Unknown embedding model identifier: {model_name}")
