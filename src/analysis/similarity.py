"""
Cosine similarity and vector retrieval utilities.
"""

from typing import List, Tuple
import numpy as np


def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """Calculates cosine similarity between two 1D vectors."""
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a < 1e-9 or norm_b < 1e-9:
        return 0.0
    dot = np.dot(vec_a, vec_b)
    val = float(dot / (norm_a * norm_b))
    return max(-1.0, min(1.0, val))


def batch_cosine_similarity(matrix_a: np.ndarray, matrix_b: np.ndarray) -> np.ndarray:
    """
    Computes pairwise cosine similarity between rows of matrix_a and matrix_b.
    Returns:
        np.ndarray: Matrix of shape (len(matrix_a), len(matrix_b)).
    """
    if matrix_a.shape[0] == 0 or matrix_b.shape[0] == 0:
        return np.empty((matrix_a.shape[0], matrix_b.shape[0]), dtype=np.float32)

    # Compute L2 norms
    norm_a = np.linalg.norm(matrix_a, axis=1, keepdims=True)
    norm_b = np.linalg.norm(matrix_b, axis=1, keepdims=True)

    norm_a = np.where(norm_a < 1e-9, 1.0, norm_a)
    norm_b = np.where(norm_b < 1e-9, 1.0, norm_b)

    unit_a = matrix_a / norm_a
    unit_b = matrix_b / norm_b

    sim_matrix = np.dot(unit_a, unit_b.T)
    return np.clip(sim_matrix, -1.0, 1.0)


def find_top_k(
    query_vec: np.ndarray,
    corpus_matrix: np.ndarray,
    top_k: int = 5,
    min_threshold: float = 0.0,
) -> List[Tuple[int, float]]:
    """
    Finds the top-K most similar items in corpus_matrix for a query vector.
    Returns:
        List of (index, similarity_score) tuples sorted in descending order of similarity.
    """
    if corpus_matrix.shape[0] == 0:
        return []

    sims = batch_cosine_similarity(query_vec.reshape(1, -1), corpus_matrix)[0]

    # Filter by minimum threshold
    valid_indices = np.where(sims >= min_threshold)[0]
    if len(valid_indices) == 0:
        return []

    # Sort descending
    sorted_idx = valid_indices[np.argsort(-sims[valid_indices])][:top_k]
    return [(int(idx), float(sims[idx])) for idx in sorted_idx]
