"""
Phase 5 Semantic Embeddings, Topic Discovery, and Narrative Intelligence Package.
"""

from src.analysis.analysis_schemas import (
    CorpusType,
    EmbeddingMetadataRecord,
    MatchStatus,
    TopicAssignmentRecord,
    TopicClusterRecord,
    TopicEvaluationMetrics,
    TopicRunRecord,
    CrossSourceMatchRecord,
    NarrativeTimelinePoint,
)
from src.analysis.embedding_models import (
    BaseEmbeddingModel,
    DeterministicTestEmbeddingModel,
    SentenceTransformerEmbeddingModel,
    get_embedding_model,
)
from src.analysis.embedding_pipeline import EmbeddingPipeline
from src.analysis.event_alignment import EventAlignmentEngine
from src.analysis.narrative_similarity import CrossSourceNarrativeMatcher
from src.analysis.narrative_timeline import NarrativeTimelineEngine
from src.analysis.similarity import batch_cosine_similarity, cosine_similarity, find_top_k
from src.analysis.tfidf_baseline import CricketTfidfBaseline
from src.analysis.topic_clustering import TopicClusterer
from src.analysis.topic_evaluation import evaluate_topic_clustering
from src.analysis.topic_labeling import TopicLabeler

__all__ = [
    "CorpusType",
    "EmbeddingMetadataRecord",
    "MatchStatus",
    "TopicAssignmentRecord",
    "TopicClusterRecord",
    "TopicEvaluationMetrics",
    "TopicRunRecord",
    "CrossSourceMatchRecord",
    "NarrativeTimelinePoint",
    "BaseEmbeddingModel",
    "DeterministicTestEmbeddingModel",
    "SentenceTransformerEmbeddingModel",
    "get_embedding_model",
    "EmbeddingPipeline",
    "EventAlignmentEngine",
    "CrossSourceNarrativeMatcher",
    "NarrativeTimelineEngine",
    "cosine_similarity",
    "batch_cosine_similarity",
    "find_top_k",
    "CricketTfidfBaseline",
    "TopicClusterer",
    "evaluate_topic_clustering",
    "TopicLabeler",
]
