"""Canonical Pydantic v2 schemas for Phase 6A Media Attention vs Performance Analytics.

Defines schemas for media attention metrics, objective cricket performance metrics,
narrative framing analysis, Attention-to-Performance Discrepancy Index (APDI),
evidence lineage, and preflight quality gates.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CohortRole(str, Enum):
    BATTER = "batter"
    BOWLER = "bowler"
    ALL_ROUNDER = "all_rounder"
    TEAM = "team"


class DiscrepancyCategory(str, Enum):
    OVER_ATTENDED = "OVER_ATTENDED"
    UNDER_ATTENDED = "UNDER_ATTENDED"
    BALANCED = "BALANCED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class SufficiencyStatus(str, Enum):
    VALID = "VALID"
    PARTIAL_COVERAGE = "PARTIAL_COVERAGE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class MediaAttentionMetrics(BaseModel):
    """Transparent, inspectable media attention metrics for a player or team."""
    model_config = ConfigDict(frozen=True)

    metric_id: str = Field(description="Unique metric ID: att_{entity_id}_{sha10}")
    entity_id: str = Field(description="Canonical player_id or team_id")
    entity_name: str = Field(description="Display name of player or team")
    entity_type: str = Field(description="'player' or 'team'")
    tournament: str = Field(default="T20 World Cup 2024")
    window_start: Optional[str] = Field(default=None)
    window_end: Optional[str] = Field(default=None)

    # 4A. Mention volume
    paragraph_count: int = Field(default=0, ge=0, description="Distinct eligible editorial paragraphs mentioning entity")
    raw_mention_count: int = Field(default=0, ge=0, description="Raw total occurrences of entity mentions")

    # 4B. Article reach within available corpus
    article_reach: int = Field(default=0, ge=0, description="Distinct articles mentioning entity in available corpus")

    # 4C. Source diversity
    source_diversity_count: int = Field(default=0, ge=0, description="Distinct publishers or source domains")
    sources: List[str] = Field(default_factory=list, description="List of distinct publisher source IDs")

    # 4D. Prominence
    prominence_score: float = Field(default=0.0, ge=0.0, description="Weighted position score (headline, lead, body)")
    headline_mentions: int = Field(default=0, ge=0, description="Mentions in article headlines")
    lead_paragraph_mentions: int = Field(default=0, ge=0, description="Mentions in opening/lead paragraphs")
    body_paragraph_mentions: int = Field(default=0, ge=0, description="Mentions in later body paragraphs")

    # 4E. Event-related attention
    event_linked_mentions: int = Field(default=0, ge=0, description="Editorial passages linked to accepted match events")

    # 4F. Temporal attention
    temporal_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="Attention counts by bucket e.g. {'pre_match': 2, 'during_match': 5, 'post_match': 10}",
    )

    article_ids: List[str] = Field(default_factory=list, description="IDs of articles contributing to attention")
    paragraph_ids: List[str] = Field(default_factory=list, description="IDs of paragraphs contributing to attention")
    raw_attention_composite: float = Field(default=0.0, ge=0.0, description="Transparent composite raw attention score")
    formula_version: str = Field(default="6A.1.0")
    created_at_utc: datetime = Field(default_factory=_utcnow)


class CricketPerformanceMetrics(BaseModel):
    """Objective cricket performance metrics derived strictly from canonical match and delivery records."""
    model_config = ConfigDict(frozen=True)

    metric_id: str = Field(description="Unique metric ID: perf_{entity_id}_{sha10}")
    entity_id: str = Field(description="Canonical player_id or team_id")
    entity_name: str = Field(description="Display name of player or team")
    entity_type: str = Field(description="'player' or 'team'")
    role: CohortRole = Field(description="batter, bowler, all_rounder, or team")
    tournament: str = Field(default="T20 World Cup 2024")
    window_start: Optional[str] = Field(default=None)
    window_end: Optional[str] = Field(default=None)

    matches_played: int = Field(default=0, ge=0)
    innings_count: int = Field(default=0, ge=0)

    # Batting statistics
    runs_scored: int = Field(default=0, ge=0)
    balls_faced: int = Field(default=0, ge=0, description="Legal balls + no-balls faced (excluding wides)")
    strike_rate: Optional[float] = Field(default=None, description="(runs / balls_faced) * 100")
    fours: int = Field(default=0, ge=0)
    sixes: int = Field(default=0, ge=0)
    dismissals: int = Field(default=0, ge=0)
    batting_average: Optional[float] = Field(default=None, description="runs / dismissals")

    # Bowling statistics
    legal_balls_bowled: int = Field(default=0, ge=0, description="Valid legal deliveries bowled")
    overs_bowled: float = Field(default=0.0, ge=0.0, description="Completed overs format (e.g. 4.2 overs)")
    runs_conceded: int = Field(default=0, ge=0, description="Runs charged to bowler (excluding byes/legbyes)")
    wickets_taken: int = Field(default=0, ge=0, description="Bowler-credited dismissals only")
    bowling_economy: Optional[float] = Field(default=None, description="(runs_conceded * 6) / legal_balls")
    bowling_average: Optional[float] = Field(default=None, description="runs_conceded / wickets")
    bowling_strike_rate: Optional[float] = Field(default=None, description="legal_balls / wickets")
    wides_conceded: int = Field(default=0, ge=0)
    noballs_conceded: int = Field(default=0, ge=0)

    # Phase-specific metrics
    powerplay_runs: int = Field(default=0, ge=0)
    powerplay_balls: int = Field(default=0, ge=0)
    powerplay_wickets: int = Field(default=0, ge=0)
    death_runs: int = Field(default=0, ge=0)
    death_balls: int = Field(default=0, ge=0)
    death_wickets: int = Field(default=0, ge=0)

    # Team outcome metrics
    team_wins: int = Field(default=0, ge=0)
    team_matches: int = Field(default=0, ge=0)
    win_percentage: Optional[float] = Field(default=None)

    raw_performance_composite: float = Field(default=0.0, description="Role-specific raw composite score")
    match_ids: List[str] = Field(default_factory=list)
    raw_stats_json: str = Field(default="{}", description="Underlying raw delivery stats dump")
    formula_version: str = Field(default="6A.1.0")
    created_at_utc: datetime = Field(default_factory=_utcnow)


class NarrativeFramingMetrics(BaseModel):
    """Sentiment and editorial narrative framing around a player or team."""
    model_config = ConfigDict(frozen=True)

    entity_id: str
    positive_count: int = Field(default=0, ge=0)
    neutral_count: int = Field(default=0, ge=0)
    negative_count: int = Field(default=0, ge=0)
    total_framed_passages: int = Field(default=0, ge=0)
    net_framing_score: float = Field(default=0.0, description="(positive - negative) / total in [-1.0, 1.0]")
    source_framing_breakdown: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    topic_distribution: Dict[str, int] = Field(default_factory=dict)
    supporting_samples: List[Dict[str, Any]] = Field(default_factory=list)


class APDIRecord(BaseModel):
    """Attention-to-Performance Discrepancy Index (APDI) evaluation for an entity."""
    model_config = ConfigDict(frozen=True)

    record_id: str = Field(description="Unique ID: apdi_{run_id}_{entity_id}")
    run_id: str = Field(description="Reference to analytics_runs.run_id")
    entity_id: str
    entity_name: str
    entity_type: str = Field(description="'player' or 'team'")
    role_cohort: CohortRole

    tournament: str = Field(default="T20 World Cup 2024")
    comparison_window: str = Field(default="tournament_overall")

    # Attention scores
    raw_attention_score: float
    normalized_attention_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    # Performance scores
    raw_performance_score: float
    normalized_performance_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    # Discrepancy Index
    apdi_value: Optional[float] = Field(default=None, ge=-1.0, le=1.0, description="NormAttention - NormPerformance")
    discrepancy_category: DiscrepancyCategory
    evidence_sufficiency_status: SufficiencyStatus

    sample_size_indicators: Dict[str, Any] = Field(
        default_factory=dict,
        description="Sample counts: paragraphs, articles, matches, balls_faced/bowled, cohort_size",
    )
    data_quality_warnings: List[str] = Field(default_factory=list)
    framing_breakdown: Dict[str, Any] = Field(default_factory=dict)
    evidence_lineage: Dict[str, Any] = Field(
        default_factory=dict,
        description="Audit trace: source IDs, match IDs, article IDs, paragraph IDs, confidence scores",
    )
    formula_version: str = Field(default="6A.1.0")
    created_at_utc: datetime = Field(default_factory=_utcnow)


class PreflightCheckResult(BaseModel):
    """Result of data eligibility and quality preflight checks."""
    model_config = ConfigDict(frozen=True)

    is_eligible: bool
    status: SufficiencyStatus
    tournament: str
    matches_count: int
    deliveries_count: int
    articles_count: int
    paragraphs_count: int
    commentary_count: int
    mentions_count: int
    resolved_mentions_count: int
    sentiment_records_count: int
    eligible_batters_count: int
    eligible_bowlers_count: int
    eligible_teams_count: int
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    checked_at_utc: datetime = Field(default_factory=_utcnow)


class AnalyticsRunRecord(BaseModel):
    """Metadata record for an analytical execution run."""
    model_config = ConfigDict(frozen=True)

    run_id: str
    status: str
    tournament: str = Field(default="T20 World Cup 2024")
    entity_type: Optional[str] = Field(default=None)
    cohorts_analyzed: List[str] = Field(default_factory=list)
    entities_processed: int = 0
    valid_apdi_count: int = 0
    insufficient_data_count: int = 0
    warnings: List[str] = Field(default_factory=list)
    started_at_utc: datetime = Field(default_factory=_utcnow)
    completed_at_utc: Optional[datetime] = None
