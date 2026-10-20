"""Canonical Data Models for T20 Cricket Intelligence Platform.

Defines Pydantic v2 schemas for all canonical entities across match facts,
unstructured commentary, journalistic news, entity resolution, and provenance.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


class WicketKind(str, Enum):
    BOWLED = "bowled"
    CAUGHT = "caught"
    LBW = "lbw"
    RUN_OUT = "run out"
    STUMPED = "stumped"
    CAUGHT_AND_BOWLED = "caught and bowled"
    HIT_WICKET = "hit wicket"
    RETIRED_HURT = "retired hurt"
    RETIRED_OUT = "retired out"
    OBSTRUCTING = "obstructing the field"
    OTHER = "other"


class MatchPhase(str, Enum):
    POWERPLAY = "powerplay"      # Overs 0-5 (Balls 0.1 - 5.6)
    MIDDLE = "middle"            # Overs 6-14 (Balls 6.1 - 14.6)
    DEATH = "death"              # Overs 15-19 (Balls 15.1 - 19.6)
    SUPER_OVER = "super_over"    # Super overs


class SourceRecord(BaseModel):
    """Immutable audit trail for raw harvest inputs."""
    model_config = ConfigDict(frozen=True)

    provenance_id: str = Field(description="Unique provenance identifier (prov_<sha256:10>)")
    source_name: str = Field(description="Name of the source e.g. cricsheet, espncricinfo, cricbuzz")
    source_identifier: str = Field(description="Filename, URL slug, or upstream match id")
    source_url: Optional[str] = Field(default=None, description="Original URL if fetched over network")
    harvest_timestamp_utc: datetime = Field(description="Exact UTC time of acquisition")
    http_status: Optional[int] = Field(default=None, description="HTTP status code if applicable")
    content_hash_sha256: str = Field(description="SHA-256 fingerprint of the raw payload")
    pipeline_version: str = Field(default="0.1.0", description="Version of the extractor/pipeline")
    license_tag: str = Field(description="Declared license of data e.g. ODbL-1.0, CC-BY-4.0")
    redistributable: bool = Field(default=False, description="Whether raw text may be redistributed")

    @field_validator("content_hash_sha256")
    @classmethod
    def validate_sha256(cls, v: str) -> str:
        if not re.fullmatch(r"[0-9a-fA-F]{64}", v):
            raise ValueError("content_hash_sha256 must be a 64-character hex string")
        return v.lower()


class IngestionRun(BaseModel):
    """Tracks execution of ingestion pipeline runs."""
    run_id: str = Field(description="Deterministic run identifier e.g. run_cricsheet_20261020_001")
    source_name: str
    status: str = Field(default="pending", description="pending, running, completed, failed")
    started_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at_utc: Optional[datetime] = None
    records_extracted: int = 0
    records_ingested: int = 0
    records_skipped: int = 0
    error_message: Optional[str] = None


class TeamRecord(BaseModel):
    """Canonical team identity."""
    model_config = ConfigDict(frozen=True)

    team_id: str = Field(description="Standardized code e.g. IND, ENG, AUS, PAK")
    name: str = Field(description="Full country/franchise name e.g. 'India'")
    aliases: List[str] = Field(default_factory=list, description="Common variations e.g. ['IND', 'Team India', 'Men in Blue']")

    @field_validator("team_id")
    @classmethod
    def validate_team_id(cls, v: str) -> str:
        v_clean = v.strip().upper()
        if not v_clean:
            raise ValueError("team_id cannot be empty")
        return v_clean


class PlayerRecord(BaseModel):
    """Canonical player identity."""
    model_config = ConfigDict(frozen=True)

    player_id: str = Field(description="Canonical ID e.g. player_virat_kohli")
    full_name: str
    cricsheet_id: Optional[str] = Field(default=None, description="8-hex Cricsheet identifier e.g. 253802")
    primary_team_id: Optional[str] = Field(default=None, description="Reference to team_id")
    batting_style: Optional[str] = None
    bowling_style: Optional[str] = None
    aliases: List[str] = Field(default_factory=list, description="Nicknames and surface variations")


class DeliveryRecord(BaseModel):
    """Structured delivery outcome from ground-truth match evidence (e.g. Cricsheet)."""
    model_config = ConfigDict(frozen=True)

    delivery_id: str = Field(description="del_{match_id}_{inn}_{over}_{ball}")
    match_id: str
    innings: int = Field(ge=1, le=4)
    over: int = Field(ge=0, le=49, description="0-indexed over number (0-19 for standard T20)")
    ball: int = Field(ge=1, description="Delivery ball index within over (1-6+)")
    batter_id: str
    bowler_id: str
    non_striker_id: Optional[str] = None
    batter_runs: int = Field(ge=0, le=7)
    extra_runs: int = Field(ge=0)
    extra_type: Optional[str] = None  # wides, noballs, byes, legbyes, penalty
    total_runs: int = Field(ge=0)
    is_legal: bool = True
    is_wicket: bool = False
    wicket_kind: Optional[str] = None
    player_dismissed_id: Optional[str] = None
    phase: MatchPhase

    @model_validator(mode="after")
    def validate_totals(self) -> DeliveryRecord:
        if self.total_runs != (self.batter_runs + self.extra_runs):
            raise ValueError(f"total_runs ({self.total_runs}) must equal batter_runs ({self.batter_runs}) + extra_runs ({self.extra_runs})")
        if self.is_wicket and not self.player_dismissed_id:
            raise ValueError("player_dismissed_id required when is_wicket is True")
        return self


class MatchRecord(BaseModel):
    """Ground-truth match metadata and scorecard facts."""
    model_config = ConfigDict(frozen=True)

    match_id: str = Field(description="Canonical ID e.g. cric_1411166 or match_2024_ind_pak")
    tournament: str
    season: str
    match_date: str = Field(description="ISO 8601 date YYYY-MM-DD")
    venue: str
    city: Optional[str] = None
    team1_id: str
    team2_id: str
    toss_winner_id: Optional[str] = None
    toss_decision: Optional[str] = None  # bat or field
    winner_id: Optional[str] = None
    win_by_runs: Optional[int] = None
    win_by_wickets: Optional[int] = None
    player_of_match_id: Optional[str] = None
    target_runs: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    provenance_id: Optional[str] = None


class CommentaryRecord(BaseModel):
    """Natural-language ball-by-ball commentary text entry."""
    model_config = ConfigDict(frozen=True)

    commentary_id: str = Field(description="comm_{match_id}_{inn}_{over}_{ball}")
    match_id: str
    innings: int = Field(ge=1)
    over: int = Field(ge=0)
    ball: int = Field(ge=1)
    bowler_raw: str
    batter_raw: str
    text: str
    event_tags: List[str] = Field(default_factory=list)  # e.g. ["FOUR", "OUT", "DRS"]
    source_domain: str
    harvest_timestamp_utc: datetime
    provenance_id: Optional[str] = None


class ArticleParagraphRecord(BaseModel):
    """Discrete paragraph segment from a cricket news report or tactical essay."""
    model_config = ConfigDict(frozen=True)

    paragraph_id: str = Field(description="{article_id}_p{index}")
    article_id: str
    paragraph_index: int = Field(ge=0)
    text: str
    char_count: int = Field(ge=1)


class ArticleRecord(BaseModel):
    """Unstructured cricket journalism document."""
    model_config = ConfigDict(frozen=True)

    article_id: str = Field(description="art_{sha256(canonical_url)[:16]}")
    canonical_url: str
    headline: str
    author: Optional[str] = None
    published_at_utc: Optional[datetime] = None
    source_domain: str
    full_text: str
    summary: Optional[str] = None
    language: str = "en"
    raw_content_hash: str
    provenance_id: Optional[str] = None

    @classmethod
    def generate_id(cls, canonical_url: str) -> str:
        clean_url = canonical_url.strip().lower()
        hash_hex = hashlib.sha256(clean_url.encode("utf-8")).hexdigest()[:16]
        return f"art_{hash_hex}"


class EventAlignmentRecord(BaseModel):
    """Traceable semantic link connecting a news paragraph to match delivery sequence."""
    model_config = ConfigDict(frozen=True)

    alignment_id: str = Field(description="align_{paragraph_id}_{match_id}_{inn}_{over}")
    paragraph_id: str
    match_id: str
    innings: int
    over_window_start: int = Field(ge=0, description="0-indexed start over")
    over_window_end: int = Field(ge=0, description="0-indexed end over")
    confidence_score: float = Field(ge=0.0, le=1.0)
    alignment_method: str = Field(default="hybrid_v1")
    supporting_evidence: Dict[str, Any] = Field(default_factory=dict)
