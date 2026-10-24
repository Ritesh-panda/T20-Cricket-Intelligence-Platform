"""Pydantic Models for Phase 6A/6B Media Attention vs Performance Analytics."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.analytics.schemas import (
    CohortRole,
    DiscrepancyCategory,
    SufficiencyStatus,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AnalyticsOverviewResponse(BaseModel):
    """High-level summary of stored analytical evaluations and preflight gate status."""
    tournament: str
    attention_metrics_count: int
    performance_metrics_count: int
    apdi_records_count: int
    over_attended_count: int
    under_attended_count: int
    balanced_count: int
    insufficient_data_count: int
    analytics_runs_count: int
    preflight_status: str
    is_eligible: bool
    warnings: List[str] = Field(default_factory=list)


class MediaAttentionResponse(BaseModel):
    """Granular media attention metrics for a player or team."""
    metric_id: str
    entity_id: str
    entity_name: str
    entity_type: str
    tournament: str
    window_start: Optional[str] = None
    window_end: Optional[str] = None
    paragraph_count: int
    raw_mention_count: int
    article_reach: int
    source_diversity_count: int
    sources: List[str] = Field(default_factory=list)
    prominence_score: float
    headline_mentions: int
    lead_paragraph_mentions: int
    body_paragraph_mentions: int
    event_linked_mentions: int
    temporal_distribution: Dict[str, int] = Field(default_factory=dict)
    article_ids: List[str] = Field(default_factory=list)
    paragraph_ids: List[str] = Field(default_factory=list)
    raw_attention_composite: float
    formula_version: str
    created_at_utc: str


class CricketPerformanceResponse(BaseModel):
    """Objective cricket performance metrics strictly derived from match records."""
    metric_id: str
    entity_id: str
    entity_name: str
    entity_type: str
    role: str
    tournament: str
    window_start: Optional[str] = None
    window_end: Optional[str] = None
    matches_played: int
    innings_count: int
    runs_scored: int
    balls_faced: int
    strike_rate: Optional[float] = None
    fours: int
    sixes: int
    dismissals: int
    batting_average: Optional[float] = None
    legal_balls_bowled: int
    overs_bowled: float
    runs_conceded: int
    wickets_taken: int
    bowling_economy: Optional[float] = None
    bowling_average: Optional[float] = None
    bowling_strike_rate: Optional[float] = None
    wides_conceded: int
    noballs_conceded: int
    powerplay_runs: int
    powerplay_balls: int
    powerplay_wickets: int
    death_runs: int
    death_balls: int
    death_wickets: int
    team_wins: int
    team_matches: int
    win_percentage: Optional[float] = None
    raw_performance_composite: float
    match_ids: List[str] = Field(default_factory=list)
    raw_stats: Dict[str, Any] = Field(default_factory=dict)
    formula_version: str
    created_at_utc: str


class NarrativeFramingResponse(BaseModel):
    """Entity-targeted sentiment and narrative framing metrics."""
    entity_id: str
    positive_count: int
    neutral_count: int
    negative_count: int
    total_framed_passages: int
    net_framing_score: float
    source_framing_breakdown: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    topic_distribution: Dict[str, int] = Field(default_factory=dict)
    supporting_samples: List[Dict[str, Any]] = Field(default_factory=list)


class APDIRecordResponse(BaseModel):
    """Attention-to-Performance Discrepancy Index evaluation and lineage."""
    record_id: str
    run_id: str
    entity_id: str
    entity_name: str
    entity_type: str
    role_cohort: str
    tournament: str
    comparison_window: str
    raw_attention_score: float
    normalized_attention_score: Optional[float] = None
    raw_performance_score: float
    normalized_performance_score: Optional[float] = None
    apdi_value: Optional[float] = None
    discrepancy_category: str
    evidence_sufficiency_status: str
    sample_size_indicators: Dict[str, Any] = Field(default_factory=dict)
    data_quality_warnings: List[str] = Field(default_factory=list)
    framing_breakdown: Dict[str, Any] = Field(default_factory=dict)
    evidence_lineage: Dict[str, Any] = Field(default_factory=dict)
    formula_version: str
    created_at_utc: str


class AnalyticsValidationResponse(BaseModel):
    """Validation report checking structural invariants across Phase 6A tables."""
    is_valid: bool
    issues: List[str] = Field(default_factory=list)
    checked_at_utc: datetime = Field(default_factory=_utcnow)
