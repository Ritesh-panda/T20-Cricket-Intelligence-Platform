"""
Topic clustering evaluation metrics module.
"""

from typing import Dict, List, Optional
import numpy as np
from sklearn.metrics import silhouette_score, davies_bouldin_score

from src.analysis.analysis_schemas import TopicEvaluationMetrics
from src.analysis.similarity import batch_cosine_similarity


def evaluate_topic_clustering(
    embeddings: np.ndarray,
    labels: np.ndarray,
    centroids: Optional[np.ndarray] = None,
) -> TopicEvaluationMetrics:
    """
    Evaluates clustering quality across geometric, density, and distribution dimensions.
    """
    n_docs = len(labels)
    if n_docs == 0:
        return TopicEvaluationMetrics(
            n_documents=0,
            n_clusters=0,
            n_noise=0,
            noise_ratio=0.0,
            notes=["Empty document set."],
        )

    unique_labels = set(labels)
    non_noise_labels = [l for l in unique_labels if l != -1]
    n_clusters = len(non_noise_labels)
    n_noise = int(np.sum(labels == -1))
    noise_ratio = float(n_noise / n_docs) if n_docs > 0 else 0.0

    notes: List[str] = []

    # Cluster sizes
    cluster_sizes: Dict[int, int] = {}
    for ul in unique_labels:
        cluster_sizes[int(ul)] = int(np.sum(labels == ul))

    non_noise_sizes = [cluster_sizes[l] for l in non_noise_labels]
    min_size = min(non_noise_sizes) if non_noise_sizes else 0
    max_size = max(non_noise_sizes) if non_noise_sizes else 0
    mean_size = float(np.mean(non_noise_sizes)) if non_noise_sizes else 0.0

    # Silhouette Score
    sil_score: Optional[float] = None
    if n_clusters >= 2 and (n_docs - n_noise) > n_clusters:
        try:
            # Evaluate only on non-noise samples
            mask = labels != -1
            if np.sum(mask) > n_clusters:
                sil_score = float(silhouette_score(embeddings[mask], labels[mask], metric="cosine"))
        except Exception as e:
            notes.append(f"Silhouette score omitted: {e}")
    else:
        notes.append("Silhouette score undefined (requires >= 2 clusters and > N_clusters non-noise points).")

    # Davies-Bouldin Index
    db_index: Optional[float] = None
    if n_clusters >= 2 and (n_docs - n_noise) > n_clusters:
        try:
            mask = labels != -1
            if np.sum(mask) > n_clusters:
                db_index = float(davies_bouldin_score(embeddings[mask], labels[mask]))
        except Exception as e:
            notes.append(f"Davies-Bouldin index omitted: {e}")
    else:
        notes.append("Davies-Bouldin index undefined.")

    # Intra-cluster similarity
    mean_intra_sim: Optional[float] = None
    if centroids is not None and len(centroids) > 0 and n_clusters > 0:
        intra_sims = []
        for i, l in enumerate(non_noise_labels):
            members = embeddings[labels == l]
            if len(members) > 0 and i < len(centroids):
                c = centroids[i].reshape(1, -1)
                sims = batch_cosine_similarity(members, c)
                intra_sims.append(float(np.mean(sims)))
        if intra_sims:
            mean_intra_sim = float(np.mean(intra_sims))

    # Inter-cluster similarity
    mean_inter_sim: Optional[float] = None
    if centroids is not None and len(centroids) >= 2:
        centroid_sims = batch_cosine_similarity(centroids, centroids)
        # Exclude self-similarity (diagonal)
        n_c = len(centroids)
        off_diag = [centroid_sims[r, c] for r in range(n_c) for c in range(n_c) if r != c]
        if off_diag:
            mean_inter_sim = float(np.mean(off_diag))

    return TopicEvaluationMetrics(
        n_documents=n_docs,
        n_clusters=n_clusters,
        n_noise=n_noise,
        noise_ratio=noise_ratio,
        silhouette_score=sil_score,
        davies_bouldin_index=db_index,
        cluster_sizes=cluster_sizes,
        min_cluster_size=min_size,
        max_cluster_size=max_size,
        mean_cluster_size=mean_size,
        mean_intra_cluster_similarity=mean_intra_sim,
        mean_inter_cluster_similarity=mean_inter_sim,
        notes=notes,
    )
