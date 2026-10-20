"""
Cross-source narrative similarity and conservative two-stage candidate retrieval and ranking.
Links editorial journalism to ball-by-ball commentary and match events.
"""

import hashlib
from typing import Any, Dict, List, Optional, Set
import numpy as np

from src.analysis.analysis_schemas import CrossSourceMatchRecord, MatchStatus
from src.analysis.similarity import find_top_k


class CrossSourceNarrativeMatcher:
    """
    Two-stage retrieval and ranking engine connecting editorial narratives with commentary entries.
    """

    def __init__(
        self,
        retrieval_threshold: float = 0.0,
        accept_threshold: float = 0.50,
        review_threshold: float = 0.35,
        model_version: str = "test-deterministic-hash-384",
    ):
        self.retrieval_threshold = retrieval_threshold
        self.accept_threshold = accept_threshold
        self.review_threshold = review_threshold
        self.model_version = model_version

    def match_editorial_to_commentary(
        self,
        editorial_norm_id: str,
        editorial_source_id: str,
        editorial_text: str,
        editorial_embedding: np.ndarray,
        editorial_entities: Set[str],
        commentary_records: List[Dict[str, Any]],
        commentary_embeddings: np.ndarray,
        top_k: int = 5,
    ) -> List[CrossSourceMatchRecord]:
        """
        Stage 1: Semantic vector retrieval (top_k candidates above retrieval_threshold).
        Stage 2: Contextual re-ranking with entity overlap and match facts.
        """
        if commentary_embeddings.shape[0] == 0:
            return []

        # Stage 1: Dense/sparse retrieval
        candidates = find_top_k(
            editorial_embedding,
            commentary_embeddings,
            top_k=top_k,
            min_threshold=self.retrieval_threshold,
        )

        results: List[CrossSourceMatchRecord] = []

        # Stage 2: Contextual re-ranking
        for idx, sem_score in candidates:
            comm = commentary_records[idx]
            comm_norm_id = comm["norm_id"]
            comm_source_id = comm["source_id"]
            comm_entities: Set[str] = comm.get("entities", set())
            match_id: Optional[str] = comm.get("match_id", None)

            evidence: Dict[str, Any] = {
                "semantic_similarity": round(float(sem_score), 4),
                "editorial_entities": sorted(list(editorial_entities)),
                "commentary_entities": sorted(list(comm_entities)),
            }

            # Check entity overlap
            shared_entities = editorial_entities.intersection(comm_entities)
            evidence["shared_entities"] = sorted(list(shared_entities))

            # Scoring formula: 0.65 * semantic_similarity + 0.35 * entity_overlap_bonus
            entity_bonus = 0.0
            if shared_entities:
                entity_bonus = min(0.35, len(shared_entities) * 0.175)
                evidence["entity_bonus"] = round(entity_bonus, 4)

            combined_score = float(0.65 * sem_score + entity_bonus)
            evidence["combined_confidence"] = round(combined_score, 4)

            # Assign resolution status conservatively
            if combined_score >= self.accept_threshold and len(shared_entities) > 0:
                status = MatchStatus.ACCEPTED
            elif combined_score >= self.review_threshold:
                status = MatchStatus.NEEDS_REVIEW
            else:
                status = MatchStatus.UNRESOLVED

            match_link_id = f"xmatch_{hashlib.sha256(f'{editorial_norm_id}_{comm_norm_id}'.encode()).hexdigest()[:16]}"

            record = CrossSourceMatchRecord(
                match_link_id=match_link_id,
                editorial_norm_id=editorial_norm_id,
                editorial_source_id=editorial_source_id,
                commentary_norm_id=comm_norm_id,
                commentary_source_id=comm_source_id,
                match_id=match_id,
                similarity_score=round(float(sem_score), 4),
                status=status,
                confidence=round(combined_score, 4),
                matching_method="two_stage_semantic_and_entity_ranking",
                evidence=evidence,
            )
            results.append(record)

        # Sort descending by combined confidence
        results.sort(key=lambda x: x.confidence, reverse=True)
        return results
