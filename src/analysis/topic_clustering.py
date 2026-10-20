"""
Modular topic clustering supporting K-Means and DBSCAN with reproducible seeds.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
from sklearn.cluster import KMeans, DBSCAN


class TopicClusterer:
    """
    Clustering engine for dense semantic embeddings or sparse TF-IDF vectors.
    """

    def __init__(
        self,
        algorithm: str = "kmeans",
        n_clusters: int = 5,
        random_state: int = 42,
        eps: float = 0.5,
        min_samples: int = 2,
    ):
        self.algorithm = algorithm.lower()
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.eps = eps
        self.min_samples = min_samples

        self.cluster_centers_: Optional[np.ndarray] = None
        self.labels_: Optional[np.ndarray] = None
        self.inertia_: Optional[float] = None

    def fit_predict(self, matrix: np.ndarray) -> np.ndarray:
        """
        Fits clusterer and assigns cluster labels to rows in matrix.
        Returns:
            np.ndarray: Array of cluster integers (0 to K-1, or -1 for noise).
        """
        n_samples = matrix.shape[0]
        if n_samples == 0:
            self.labels_ = np.empty(0, dtype=int)
            self.cluster_centers_ = np.empty((0, matrix.shape[1] if matrix.ndim > 1 else 0))
            return self.labels_

        # Edge case: single document
        if n_samples == 1:
            self.labels_ = np.zeros(1, dtype=int)
            self.cluster_centers_ = matrix.copy()
            self.inertia_ = 0.0
            return self.labels_

        if self.algorithm == "kmeans":
            effective_k = min(self.n_clusters, n_samples)
            kmeans = KMeans(
                n_clusters=effective_k,
                random_state=self.random_state,
                n_init=10,
                max_iter=300,
            )
            self.labels_ = kmeans.fit_predict(matrix)
            self.cluster_centers_ = kmeans.cluster_centers_
            self.inertia_ = float(kmeans.inertia_)
            return self.labels_

        elif self.algorithm == "dbscan":
            dbscan = DBSCAN(
                eps=self.eps,
                min_samples=self.min_samples,
                metric="cosine",
            )
            self.labels_ = dbscan.fit_predict(matrix)
            # Compute empirical centroids for non-noise clusters
            unique_labels = [l for l in np.unique(self.labels_) if l != -1]
            if unique_labels:
                centers = []
                for ul in unique_labels:
                    cluster_members = matrix[self.labels_ == ul]
                    mean_center = cluster_members.mean(axis=0)
                    norm = np.linalg.norm(mean_center)
                    if norm > 1e-9:
                        mean_center = mean_center / norm
                    centers.append(mean_center)
                self.cluster_centers_ = np.array(centers, dtype=np.float32)
            else:
                self.cluster_centers_ = np.empty((0, matrix.shape[1]), dtype=np.float32)
            self.inertia_ = None
            return self.labels_

        else:
            raise ValueError(f"Unsupported clustering algorithm: {self.algorithm}")

    def compute_distances_to_centroid(self, matrix: np.ndarray) -> np.ndarray:
        """Computes Euclidean distance from each sample to its assigned cluster centroid."""
        if self.labels_ is None or self.cluster_centers_ is None:
            raise RuntimeError("Clusterer must be fitted before computing distances.")

        n_samples = matrix.shape[0]
        distances = np.zeros(n_samples, dtype=np.float32)

        for i in range(n_samples):
            lbl = self.labels_[i]
            if lbl == -1:
                # Noise point
                distances[i] = 1.0
            elif lbl < len(self.cluster_centers_):
                centroid = self.cluster_centers_[lbl]
                distances[i] = float(np.linalg.norm(matrix[i] - centroid))
            else:
                distances[i] = 0.0

        return distances
