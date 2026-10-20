"""
Topic labeling and representative document selection using class-based TF-IDF (c-TF-IDF).
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer

from src.analysis.tfidf_baseline import CRICKET_TOKEN_PATTERN


class TopicLabeler:
    """
    Computes class-based TF-IDF (c-TF-IDF) keyword representations and human-readable labels.
    """

    def __init__(self, top_n_words: int = 5):
        self.top_n_words = top_n_words

    def extract_cluster_keywords(
        self,
        documents: List[str],
        labels: np.ndarray,
    ) -> Dict[int, List[str]]:
        """
        Extracts salient keywords for each cluster using c-TF-IDF.
        Returns:
            Dict mapping cluster_id -> list of top keyword strings.
        """
        unique_labels = sorted(list(set(labels)))
        cluster_docs: Dict[int, str] = {}

        for ul in unique_labels:
            if ul == -1:
                continue
            # Join all docs in this cluster into one pseudo-document
            members = [documents[i] for i in range(len(documents)) if labels[i] == ul]
            cluster_docs[ul] = " ".join(members)

        if not cluster_docs:
            return {}

        cluster_keys = list(cluster_docs.keys())
        corpus = [cluster_docs[k] for k in cluster_keys]

        try:
            cv = CountVectorizer(
                token_pattern=CRICKET_TOKEN_PATTERN,
                ngram_range=(1, 2),
                stop_words="english",
                min_df=1,
            )
            count_matrix = cv.fit_transform(corpus).toarray()
            words = cv.get_feature_names_out()

            if count_matrix.shape[1] == 0:
                return {k: [] for k in cluster_keys}

            # c-TF-IDF calculation
            # tf: frequency of word in cluster / total words in cluster
            total_words_per_cluster = count_matrix.sum(axis=1, keepdims=True)
            total_words_per_cluster = np.where(total_words_per_cluster == 0, 1, total_words_per_cluster)
            tf = count_matrix / total_words_per_cluster

            # idf: log(1 + (avg words per cluster / frequency of word across all clusters))
            avg_words = count_matrix.sum() / len(cluster_keys)
            word_freq_all = count_matrix.sum(axis=0)
            word_freq_all = np.where(word_freq_all == 0, 1, word_freq_all)
            idf = np.log(1.0 + (avg_words / word_freq_all))

            c_tfidf = tf * idf

            result = {}
            for row_idx, clus_id in enumerate(cluster_keys):
                scores = c_tfidf[row_idx]
                top_indices = np.argsort(-scores)[:self.top_n_words]
                keywords = [str(words[idx]) for idx in top_indices if scores[idx] > 0]
                result[clus_id] = keywords

            return result

        except Exception:
            # Fallback if vocabulary extraction fails
            return {k: [] for k in cluster_keys}

    def generate_topic_label(self, keywords: List[str], cluster_id: int) -> str:
        """
        Creates a concise human-readable topic label from top keywords.
        """
        if cluster_id == -1:
            return "Outliers / Noise"
        if not keywords:
            return f"Unlabelled Cluster {cluster_id}"

        # Join up to top 3 keywords with hyphen
        top_k = [w.replace(" ", "_") for w in keywords[:3]]
        return "-".join(top_k)

    def select_representative_documents(
        self,
        doc_ids: List[str],
        labels: np.ndarray,
        distances: np.ndarray,
        cluster_id: int,
        top_m: int = 3,
    ) -> List[str]:
        """
        Selects document IDs closest to cluster centroid.
        """
        if cluster_id == -1:
            return []

        indices = [i for i in range(len(doc_ids)) if labels[i] == cluster_id]
        if not indices:
            return []

        # Sort by distance ascending (closest first)
        sorted_indices = sorted(indices, key=lambda idx: distances[idx])
        return [doc_ids[idx] for idx in sorted_indices[:top_m]]
