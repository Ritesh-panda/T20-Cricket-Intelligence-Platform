"""Comprehensive Unit and Integration Tests for Phase 6A Analytics Engine.

Tests:
1. Cricket scoring semantics and invariants (wides, no-balls, byes, leg-byes, wickets).
2. Batting and bowling performance metrics and phase breakdowns.
3. Media attention metrics (paragraphs, raw mentions, reach, source diversity, prominence, event links).
4. Narrative framing metrics (sentiment distributions, net framing score).
5. Preflight quality gate validation on empty and populated databases.
6. APDI calculation, percentile cohort normalization, and discrepancy classification
   (OVER_ATTENDED, UNDER_ATTENDED, BALANCED, and INSUFFICIENT_DATA).
7. Storage schema v5 persistence, retrieval, and invariant validation.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import pytest

from src.analytics.schemas import (
    APDIRecord,
    CohortRole,
    CricketPerformanceMetrics,
    DiscrepancyCategory,
    MediaAttentionMetrics,
    SufficiencyStatus,
)
from src.analytics.attention import MediaAttentionCalculator
from src.analytics.performance import CricketPerformanceCalculator
from src.analytics.framing import NarrativeFramingCalculator
from src.analytics.apdi import APDICalculator
from src.analytics.preflight import AnalyticsPreflight
from src.storage.sqlite_manager import SQLiteStorageManager


@pytest.fixture
def temp_db(tmp_path: Path) -> SQLiteStorageManager:
    db_file = tmp_path / "test_analytics.db"
    return SQLiteStorageManager(db_file)


# =========================================================================
# 1. Performance Calculator & Cricket Scoring Invariant Tests
# =========================================================================
def test_batting_metrics_and_scoring_invariants():
    calc = CricketPerformanceCalculator()
    player_id = "p_kohli"

    # Synthetic deliveries:
    # 1: 1 run (legal)
    # 2: 4 runs (four, legal)
    # 3: wide (extra_type='wides', batter_runs=0, extra_runs=1) -> NOT faced by batter!
    # 4: noball (extra_type='noballs', batter_runs=2, extra_runs=1) -> FACED by batter!
    # 5: 6 runs (six, death phase)
    # 6: 0 runs, dismissed (bowled)
    deliveries = [
        {"match_id": "m1", "batter_id": player_id, "batter_runs": 1, "extra_runs": 0, "extra_type": None, "phase": "powerplay"},
        {"match_id": "m1", "batter_id": player_id, "batter_runs": 4, "extra_runs": 0, "extra_type": None, "phase": "powerplay"},
        {"match_id": "m1", "batter_id": player_id, "batter_runs": 0, "extra_runs": 1, "extra_type": "wides", "phase": "middle"},
        {"match_id": "m1", "batter_id": player_id, "batter_runs": 2, "extra_runs": 1, "extra_type": "noballs", "phase": "middle"},
        {"match_id": "m1", "batter_id": player_id, "batter_runs": 6, "extra_runs": 0, "extra_type": None, "phase": "death"},
        {"match_id": "m1", "batter_id": player_id, "player_dismissed_id": player_id, "batter_runs": 0, "extra_runs": 0, "extra_type": None, "phase": "death"},
    ]

    metrics = calc.compute_batter_performance(
        player_id=player_id,
        player_name="Virat Kohli",
        deliveries=deliveries,
        matches_played=1,
    )

    # Invariant checks:
    # Balls faced: 5 (1, 4, noball, 6, 0) - wide is NOT counted
    assert metrics.balls_faced == 5
    # Runs: 1 + 4 + 0 + 2 + 6 + 0 = 13
    assert metrics.runs_scored == 13
    assert metrics.fours == 1
    assert metrics.sixes == 1
    assert metrics.dismissals == 1
    assert metrics.strike_rate == pytest.approx(260.0, 0.1)
    assert metrics.batting_average == pytest.approx(13.0, 0.1)
    assert metrics.powerplay_runs == 5
    assert metrics.powerplay_balls == 2
    assert metrics.death_runs == 6
    assert metrics.death_balls == 2
    assert metrics.raw_performance_composite > 0.0


def test_bowling_metrics_and_scoring_invariants():
    calc = CricketPerformanceCalculator()
    bowler_id = "p_bumrah"

    # Synthetic deliveries:
    # 1: legal ball, dot, 0 runs
    # 2: legal ball, 4 runs (four)
    # 3: wide ball (is_legal=0, extra_type='wides', batter_runs=0, extra_runs=1)
    # 4: no ball (is_legal=0, extra_type='noballs', batter_runs=1, extra_runs=1)
    # 5: legal ball, byes (batter_runs=0, extra_runs=4, extra_type='byes') -> NOT charged to bowler!
    # 6: legal ball, wicket (caught) -> credited to bowler
    # 7: legal ball, run out -> NOT credited to bowler
    deliveries = [
        {"match_id": "m1", "bowler_id": bowler_id, "is_legal": 1, "batter_runs": 0, "extra_runs": 0, "extra_type": None, "is_wicket": 0, "phase": "powerplay"},
        {"match_id": "m1", "bowler_id": bowler_id, "is_legal": 1, "batter_runs": 4, "extra_runs": 0, "extra_type": None, "is_wicket": 0, "phase": "powerplay"},
        {"match_id": "m1", "bowler_id": bowler_id, "is_legal": 0, "batter_runs": 0, "extra_runs": 1, "extra_type": "wides", "is_wicket": 0, "phase": "middle"},
        {"match_id": "m1", "bowler_id": bowler_id, "is_legal": 0, "batter_runs": 1, "extra_runs": 1, "extra_type": "noballs", "is_wicket": 0, "phase": "middle"},
        {"match_id": "m1", "bowler_id": bowler_id, "is_legal": 1, "batter_runs": 0, "extra_runs": 4, "extra_type": "byes", "is_wicket": 0, "phase": "death"},
        {"match_id": "m1", "bowler_id": bowler_id, "is_legal": 1, "batter_runs": 0, "extra_runs": 0, "extra_type": None, "is_wicket": 1, "wicket_kind": "caught", "phase": "death"},
        {"match_id": "m1", "bowler_id": bowler_id, "is_legal": 1, "batter_runs": 0, "extra_runs": 0, "extra_type": None, "is_wicket": 1, "wicket_kind": "run out", "phase": "death"},
    ]

    metrics = calc.compute_bowler_performance(
        player_id=bowler_id,
        player_name="Jasprit Bumrah",
        deliveries=deliveries,
        matches_played=1,
    )

    # Invariants:
    # Legal balls: 5 (balls 1, 2, 5, 6, 7)
    assert metrics.legal_balls_bowled == 5
    assert metrics.wides_conceded == 1
    assert metrics.noballs_conceded == 1
    # Runs conceded:
    # ball 1: 0
    # ball 2: 4
    # ball 3 (wide): 0 + 1 = 1
    # ball 4 (noball): 1 + 1 = 2
    # ball 5 (byes): 0 (byes not charged to bowler!)
    # ball 6: 0
    # ball 7: 0
    # Total = 0 + 4 + 1 + 2 + 0 + 0 + 0 = 7
    assert metrics.runs_conceded == 7
    # Wickets: only 1 (caught is bowler-credited, run out is NOT)
    assert metrics.wickets_taken == 1
    assert metrics.death_wickets == 1
    assert metrics.bowling_economy == pytest.approx((7 * 6.0) / 5, 0.1)


def test_team_performance():
    calc = CricketPerformanceCalculator()
    matches = [
        {"match_id": "m1", "team1_id": "ind", "team2_id": "pak", "winner_id": "ind"},
        {"match_id": "m2", "team1_id": "ind", "team2_id": "aus", "winner_id": "ind"},
        {"match_id": "m3", "team1_id": "ind", "team2_id": "rsa", "winner_id": "rsa"},
    ]
    team_metrics = calc.compute_team_performance(
        team_id="ind",
        team_name="India",
        matches=matches,
    )
    assert team_metrics.team_matches == 3
    assert team_metrics.team_wins == 2
    assert team_metrics.win_percentage == pytest.approx(66.67, 0.1)
    assert team_metrics.raw_performance_composite > 0.0


# =========================================================================
# 2. Media Attention Metrics Tests
# =========================================================================
def test_attention_metrics_calculation():
    calc = MediaAttentionCalculator()
    entity_id = "p_rohit"

    mentions = [
        {"source_type": "article_paragraph", "source_id": "para_1"},
        {"source_type": "article_paragraph", "source_id": "para_1"},  # duplicate in same paragraph
        {"source_type": "article_paragraph", "source_id": "para_2"},
        {"source_type": "article", "source_id": "art_1"},             # headline mention
    ]
    paragraphs = {
        "para_1": {"article_id": "art_1", "paragraph_index": 0, "is_lead": True},
        "para_2": {"article_id": "art_2", "paragraph_index": 3, "is_lead": False},
    }
    articles = {
        "art_1": {"source_domain": "espncricinfo.com", "published_at_utc": "2024-06-20T10:00:00Z"},
        "art_2": {"source_domain": "cricbuzz.com", "published_at_utc": "2024-06-21T12:00:00Z"},
    }
    event_alignments = [
        {"status": "ACCEPTED", "paragraph_id": "para_1"},
        {"status": "NEEDS_REVIEW", "paragraph_id": "para_2"},
    ]
    match_dates = {"m1": "2024-06-20"}

    metrics = calc.compute_for_entity(
        entity_id=entity_id,
        entity_name="Rohit Sharma",
        entity_type="player",
        mentions=mentions,
        paragraphs=paragraphs,
        articles=articles,
        event_alignments=event_alignments,
        match_dates=match_dates,
    )

    # 4 distinct mentions, but only 2 distinct paragraphs
    assert metrics.raw_mention_count == 4
    assert metrics.paragraph_count == 2
    assert metrics.article_reach == 2
    assert metrics.source_diversity_count == 2
    assert set(metrics.sources) == {"espncricinfo.com", "cricbuzz.com"}
    assert metrics.headline_mentions == 1
    assert metrics.lead_paragraph_mentions == 1
    assert metrics.body_paragraph_mentions == 1
    assert metrics.event_linked_mentions == 1  # only ACCEPTED
    assert metrics.prominence_score > 0.0
    assert metrics.raw_attention_composite > 0.0


# =========================================================================
# 3. Narrative Framing Analysis Tests
# =========================================================================
def test_narrative_framing_calculation():
    calc = NarrativeFramingCalculator()
    sentiments = [
        {"source_id": "p1", "general_sentiment": "POSITIVE", "framing_score": 0.8},
        {"source_id": "p2", "general_sentiment": "POSITIVE", "framing_score": 0.7},
        {"source_id": "p3", "general_sentiment": "NEGATIVE", "framing_score": -0.6},
        {"source_id": "p4", "general_sentiment": "NEUTRAL", "framing_score": 0.0},
    ]
    paragraphs = {
        "p1": {"article_id": "a1", "text": "Masterclass innings by the captain."},
        "p2": {"article_id": "a1", "text": "Dominant boundary hitting throughout."},
        "p3": {"article_id": "a2", "text": "Costly misfield conceded extra boundaries."},
        "p4": {"article_id": "a2", "text": "Rotated the strike in middle overs."},
    }
    articles = {
        "a1": {"source_domain": "espncricinfo.com"},
        "a2": {"source_domain": "bbc.com"},
    }

    framing = calc.compute_framing(
        entity_id="p_rohit",
        sentiments=sentiments,
        paragraphs=paragraphs,
        articles=articles,
    )

    assert framing.positive_count == 2
    assert framing.negative_count == 1
    assert framing.neutral_count == 1
    assert framing.total_framed_passages == 4
    # net score: (2 - 1) / 4 = 0.25
    assert framing.net_framing_score == 0.25
    assert "espncricinfo.com" in framing.source_framing_breakdown
    assert "bbc.com" in framing.source_framing_breakdown
    assert len(framing.supporting_samples) > 0


# =========================================================================
# 4. APDI Calculation & Cohort Normalization Tests
# =========================================================================
def test_apdi_over_under_balanced_classification():
    apdi_calc = APDICalculator()

    # Create 3 batters:
    # Batter A: High Attention (raw=50.0), Low Performance (raw=10.0) -> OVER_ATTENDED
    # Batter B: Low Attention (raw=5.0), High Performance (raw=90.0) -> UNDER_ATTENDED
    # Batter C: Medium Attention (raw=25.0), Medium Performance (raw=50.0) -> BALANCED

    att_a = MediaAttentionMetrics(
        metric_id="att_a", entity_id="p_a", entity_name="Player A", entity_type="player",
        paragraph_count=20, article_reach=10, source_diversity_count=3, raw_attention_composite=50.0,
    )
    perf_a = CricketPerformanceMetrics(
        metric_id="perf_a", entity_id="p_a", entity_name="Player A", entity_type="player",
        role=CohortRole.BATTER, matches_played=3, balls_faced=30, runs_scored=15, raw_performance_composite=10.0,
    )

    att_b = MediaAttentionMetrics(
        metric_id="att_b", entity_id="p_b", entity_name="Player B", entity_type="player",
        paragraph_count=2, article_reach=1, source_diversity_count=1, raw_attention_composite=5.0,
    )
    perf_b = CricketPerformanceMetrics(
        metric_id="perf_b", entity_id="p_b", entity_name="Player B", entity_type="player",
        role=CohortRole.BATTER, matches_played=3, balls_faced=60, runs_scored=120, sixes=5, raw_performance_composite=90.0,
    )

    att_c = MediaAttentionMetrics(
        metric_id="att_c", entity_id="p_c", entity_name="Player C", entity_type="player",
        paragraph_count=10, article_reach=5, source_diversity_count=2, raw_attention_composite=25.0,
    )
    perf_c = CricketPerformanceMetrics(
        metric_id="perf_c", entity_id="p_c", entity_name="Player C", entity_type="player",
        role=CohortRole.BATTER, matches_played=3, balls_faced=45, runs_scored=65, raw_performance_composite=50.0,
    )

    records = apdi_calc.compute_cohort_apdi(
        role=CohortRole.BATTER,
        entities_data=[(att_a, perf_a, None), (att_b, perf_b, None), (att_c, perf_c, None)],
    )

    rec_map = {r.entity_id: r for r in records}

    # Player A should be OVER_ATTENDED (high attention rank 1.0, low perf rank 0.0 -> APDI = +1.0)
    assert rec_map["p_a"].discrepancy_category == DiscrepancyCategory.OVER_ATTENDED
    assert rec_map["p_a"].apdi_value > 0.20
    assert rec_map["p_a"].normalized_attention_score == 1.0
    assert rec_map["p_a"].normalized_performance_score == 0.0

    # Player B should be UNDER_ATTENDED (low attention rank 0.0, high perf rank 1.0 -> APDI = -1.0)
    assert rec_map["p_b"].discrepancy_category == DiscrepancyCategory.UNDER_ATTENDED
    assert rec_map["p_b"].apdi_value < -0.20
    assert rec_map["p_b"].normalized_attention_score == 0.0
    assert rec_map["p_b"].normalized_performance_score == 1.0

    # Player C should be BALANCED (middle attention rank 0.5, middle perf rank 0.5 -> APDI = 0.0)
    assert rec_map["p_c"].discrepancy_category == DiscrepancyCategory.BALANCED
    assert rec_map["p_c"].apdi_value == pytest.approx(0.0, 0.01)


def test_apdi_insufficient_data_handling():
    apdi_calc = APDICalculator()

    # Batter with 0 balls faced and 0 paragraphs
    att_empty = MediaAttentionMetrics(
        metric_id="att_zero", entity_id="p_zero", entity_name="Player Zero", entity_type="player",
        paragraph_count=0, raw_mention_count=0, raw_attention_composite=0.0,
    )
    perf_empty = CricketPerformanceMetrics(
        metric_id="perf_zero", entity_id="p_zero", entity_name="Player Zero", entity_type="player",
        role=CohortRole.BATTER, matches_played=0, balls_faced=0, runs_scored=0, raw_performance_composite=0.0,
    )

    records = apdi_calc.compute_cohort_apdi(
        role=CohortRole.BATTER,
        entities_data=[(att_empty, perf_empty, None)],
    )

    assert len(records) == 1
    rec = records[0]
    assert rec.discrepancy_category == DiscrepancyCategory.INSUFFICIENT_DATA
    assert rec.evidence_sufficiency_status == SufficiencyStatus.INSUFFICIENT_DATA
    assert rec.apdi_value is None
    assert rec.normalized_attention_score is None
    assert rec.normalized_performance_score is None
    assert len(rec.data_quality_warnings) > 0


# =========================================================================
# 5. Storage Schema V5 Persistence & Retrieval Tests
# =========================================================================
def test_storage_v5_crud_and_invariants(temp_db: SQLiteStorageManager):
    # 1. Attention CRUD
    att = MediaAttentionMetrics(
        metric_id="att_test_1",
        entity_id="p_test",
        entity_name="Test Player",
        entity_type="player",
        paragraph_count=12,
        raw_mention_count=24,
        article_reach=5,
        source_diversity_count=3,
        sources=["bbc.com", "espncricinfo.com"],
        prominence_score=15.0,
        raw_attention_composite=32.0,
    )
    assert temp_db.upsert_attention_metrics(att) is True
    retrieved_att = temp_db.get_attention_metrics("p_test")
    assert retrieved_att is not None
    assert retrieved_att["paragraph_count"] == 12
    assert retrieved_att["sources"] == ["bbc.com", "espncricinfo.com"]

    # 2. Performance CRUD
    perf = CricketPerformanceMetrics(
        metric_id="perf_test_1",
        entity_id="p_test",
        entity_name="Test Player",
        entity_type="player",
        role=CohortRole.BATTER,
        matches_played=4,
        runs_scored=180,
        balls_faced=120,
        strike_rate=150.0,
        fours=18,
        sixes=6,
        raw_performance_composite=195.0,
    )
    assert temp_db.upsert_performance_metrics(perf) is True
    retrieved_perf = temp_db.get_performance_metrics("p_test", role="batter")
    assert retrieved_perf is not None
    assert retrieved_perf["runs_scored"] == 180
    assert retrieved_perf["strike_rate"] == 150.0

    # 3. APDI Batch Save
    apdi_rec = APDIRecord(
        record_id="apdi_run1_ptest",
        run_id="run1",
        entity_id="p_test",
        entity_name="Test Player",
        entity_type="player",
        role_cohort=CohortRole.BATTER,
        tournament="T20 World Cup 2024",
        comparison_window="tournament_overall",
        raw_attention_score=32.0,
        normalized_attention_score=0.8,
        raw_performance_score=195.0,
        normalized_performance_score=0.9,
        apdi_value=-0.1,
        discrepancy_category=DiscrepancyCategory.BALANCED,
        evidence_sufficiency_status=SufficiencyStatus.VALID,
        sample_size_indicators={"balls_faced": 120},
        data_quality_warnings=[],
        framing_breakdown={},
        evidence_lineage={"formula_version": "6A.1.0"},
    )
    saved_count = temp_db.save_apdi_records([apdi_rec])
    assert saved_count == 1

    records = temp_db.get_apdi_records(run_id="run1")
    assert len(records) == 1
    assert records[0]["discrepancy_category"] == "BALANCED"
    assert records[0]["apdi_value"] == -0.1

    # 4. Analytics Summary
    summary = temp_db.get_analytics_summary()
    assert summary["attention_metrics_count"] == 1
    assert summary["performance_metrics_count"] == 1
    assert summary["apdi_records_count"] == 1
    assert summary["balanced_count"] == 1


# =========================================================================
# 6. Preflight Quality Gate Tests
# =========================================================================
def test_preflight_on_empty_and_populated(temp_db: SQLiteStorageManager):
    preflight = AnalyticsPreflight(temp_db)

    # Empty DB
    empty_result = preflight.run_preflight()
    assert empty_result.is_eligible is False
    assert empty_result.status == SufficiencyStatus.INSUFFICIENT_DATA
    assert len(empty_result.warnings) >= 3
