"""Pydantic Models for Topics, Entity Mentions, Timeline Snapshots, and Alignments."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TopicClusterResponse(BaseModel):
    """Discovered semantic topic cluster."""
    cluster_id: str
    run_id: str
    cluster_index: int
    topic_label: str
    keywords: List[str] = Field(default_factory=list)
    doc_count: int
    representative_doc_ids: List[str] = Field(default_factory=list)
    intra_cluster_similarity: Optional[float] = None
    is_noise: bool = False


class EntityMentionResponse(BaseModel):
    """Entity mention extracted from source texts."""
    mention_id: str
    source_type: str
    source_id: str
    entity_type: str
    surface_text: str
    start_char: int
    end_char: int
    detection_method: str
    confidence: float
    resolved_id: Optional[str] = None
    resolution_status: str
    evidence: Dict[str, Any] = Field(default_factory=dict)
    pipeline_version: str
    created_at_utc: str


class NarrativeTimelineResponse(BaseModel):
    """Narrative evolution point in time."""
    snapshot_id: str
    bucket_label: str
    doc_count: int
    mean_sentiment: float
    sentiment_distribution: Dict[str, int] = Field(default_factory=dict)
    top_topics: List[Any] = Field(default_factory=list)
    top_entities: List[Any] = Field(default_factory=list)
    match_events_count: int = 0
    observed_timestamps_count: int = 0
    inferred_timestamps_count: int = 0
    created_at_utc: str


class CrossSourceMatchResponse(BaseModel):
    """Cross-source alignment link between editorial passages and commentary/match facts."""
    match_link_id: str
    editorial_norm_id: str
    editorial_source_id: str
    commentary_norm_id: str
    commentary_source_id: str
    match_id: Optional[str] = None
    similarity_score: float
    status: str
    confidence: float
    matching_method: str
    evidence: Dict[str, Any] = Field(default_factory=dict)
    created_at_utc: str
