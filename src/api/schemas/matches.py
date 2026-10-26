"""Pydantic Models for Matches, Deliveries, and Match Scorecards."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MatchResponse(BaseModel):
    """Canonical match scorecard record."""
    match_id: str
    tournament: str
    season: str
    match_date: str
    venue: str
    city: Optional[str] = None
    team1_id: str
    team2_id: str
    toss_winner_id: Optional[str] = None
    toss_decision: Optional[str] = None
    winner_id: Optional[str] = None
    win_by_runs: Optional[int] = None
    win_by_wickets: Optional[int] = None
    player_of_match_id: Optional[str] = None
    target_runs: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    provenance_id: Optional[str] = None


class DeliveryResponse(BaseModel):
    """Structured delivery fact record."""
    delivery_id: str
    match_id: str
    innings: int
    over_num: int
    ball_num: int
    batter_id: str
    bowler_id: str
    non_striker_id: Optional[str] = None
    batter_runs: int
    extra_runs: int
    extra_type: Optional[str] = None
    total_runs: int
    is_legal: bool
    is_wicket: bool
    wicket_kind: Optional[str] = None
    player_dismissed_id: Optional[str] = None
    phase: str


class MatchBatterScore(BaseModel):
    player_id: str
    player_name: Optional[str] = None
    team_id: Optional[str] = None
    innings: Optional[int] = None
    runs: int
    balls: int
    fours: int
    sixes: int
    strike_rate: Optional[float] = None
    is_out: bool
    dismissal_kind: Optional[str] = None


class MatchBowlerScore(BaseModel):
    player_id: str
    player_name: Optional[str] = None
    team_id: Optional[str] = None
    innings: Optional[int] = None
    overs: float
    legal_balls: int
    maidens: Optional[int] = 0
    runs_conceded: int
    wickets: int
    economy: Optional[float] = None


class MatchTeamScore(BaseModel):
    team_id: str
    innings: int
    total_runs: int
    total_wickets: int
    legal_overs: float
    extras: Optional[int] = 0


class MatchPerformanceScorecard(BaseModel):
    """Aggregated match scorecard and player performance breakdown."""
    match_id: str
    tournament: str
    match_date: str
    venue: str
    winner_id: Optional[str] = None
    team_scores: List[MatchTeamScore] = Field(default_factory=list)
    batters: List[MatchBatterScore] = Field(default_factory=list)
    bowlers: List[MatchBowlerScore] = Field(default_factory=list)
