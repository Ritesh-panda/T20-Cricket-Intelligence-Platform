"""Pydantic v2 Canonical Schemas for NLP Processing Layer.

Defines schemas for normalized text records, entity mentions, resolution decisions,
sentiment and framing baselines, and NLP pipeline runs.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class EntityType(str, Enum):
    PLAYER = "PLAYER"
    TEAM = "TEAM"
    VENUE = "VENUE"
    TOURNAMENT = "TOURNAMENT"
    PHASE = "PHASE"


class ResolutionStatus(str, Enum):
    RESOLVED = "RESOLVED"
    AMBIGUOUS = "AMBIGUOUS"
    UNRESOLVED = "UNRESOLVED"
    REJECTED = "REJECTED"


class SentimentLabel(str, Enum):
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"


class NormalizedTextRecord(BaseModel):
    """Normalized text with preserved reference to source span and original content."""
    model_config = ConfigDict(frozen=True)

    norm_id: str = Field(description="Unique normalized record ID e.g. norm_art_123_p0_v1")
    source_type: str = Field(description="article, article_paragraph, commentary_entry")
    source_id: str = Field(description="Unique ID of source record (e.g. paragraph_id or commentary_id)")
    original_text: str = Field(description="Exact raw text prior to normalization")
    normalized_text: str = Field(description="Cleaned, standardized text")
    char_count: int = Field(ge=0)
    pipeline_version: str = Field(default="0.1.0")
    processed_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EntityMentionRecord(BaseModel):
    """Exact character-span mention of a cricket entity within source text."""
    model_config = ConfigDict(frozen=True)

    mention_id: str = Field(description="Unique mention ID e.g. men_{source_id}_{start}_{end}")
    source_type: str
    source_id: str
    entity_type: EntityType
    surface_text: str = Field(description="Verbatim text span in source document")
    start_char: int = Field(ge=0, description="Start character offset")
    end_char: int = Field(ge=0, description="End character offset")
    detection_method: str = Field(default="boundary_gazetteer", description="exact_gazetteer, boundary_regex, heuristic")
    confidence: float = Field(ge=0.0, le=1.0)
    resolved_id: Optional[str] = Field(default=None, description="Resolved canonical entity ID if resolved")
    resolution_status: ResolutionStatus = Field(default=ResolutionStatus.UNRESOLVED)
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Diagnostics, matched alias, candidate scores")
    pipeline_version: str = Field(default="0.1.0")
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("end_char")
    @classmethod
    def validate_span(cls, v: int, info: Any) -> int:
        start = info.data.get("start_char", 0)
        if v < start:
            raise ValueError(f"end_char ({v}) must be >= start_char ({start})")
        return v


class EntityResolutionRecord(BaseModel):
    """Audit record evaluating candidate canonical identities for a detected mention."""
    model_config = ConfigDict(frozen=True)

    resolution_id: str = Field(description="res_{mention_id}_{candidate_id}")
    mention_id: str
    candidate_id: str
    entity_type: EntityType
    score: float = Field(ge=0.0, le=1.0)
    is_winner: bool = Field(default=False)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SentimentBaselineRecord(BaseModel):
    """Entity-targeted and general framing baseline output."""
    model_config = ConfigDict(frozen=True)

    sentiment_id: str = Field(description="sent_{source_id}_{target_or_doc}")
    source_type: str
    source_id: str
    target_entity_id: Optional[str] = Field(default=None, description="Resolved player or team ID if aspect-targeted")
    general_sentiment: SentimentLabel
    event_polarity: SentimentLabel = Field(description="Factual polarity of cricket event e.g. wicket/boundary")
    framing_score: float = Field(ge=-1.0, le=1.0, description="Continuous framing score: -1.0 (adverse) to +1.0 (dominant)")
    compound_score: float = Field(ge=-1.0, le=1.0)
    evidence_tokens: List[str] = Field(default_factory=list)
    rule_applied: str = Field(default="cricket_lexicon_baseline_v1")
    confidence: float = Field(ge=0.0, le=1.0)
    pipeline_version: str = Field(default="0.1.0")
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class NLPRunRecord(BaseModel):
    """Tracks NLP processing execution runs."""
    run_id: str
    status: str = Field(default="running")
    started_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at_utc: Optional[datetime] = None
    records_processed: int = 0
    mentions_extracted: int = 0
    sentiment_scored: int = 0
    errors: List[str] = Field(default_factory=list)
