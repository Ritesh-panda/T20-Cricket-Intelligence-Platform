"""Phase 7 Real-World Data Ingestion and End-to-End Validation Tests.

Validates:
1. Ingestion of genuine Cricsheet matches into an isolated SQLite database.
2. Scorecard reconciliation and delivery referential integrity.
3. Ingestion idempotency: repeated ingestion does not produce duplicate rows.
4. Editorial article parsing, paragraph segmentation, and match linking.
5. APDI computation, percentile normalization, and Insufficient Data handling.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
import pytest

from src.adapters.cricsheet_adapter import CricsheetAdapter
from src.adapters.news_adapter import NewsArticleAdapter
from src.analytics.apdi import APDICalculator
from src.analytics.performance import CricketPerformanceCalculator
from src.analytics.schemas import CohortRole, CricketPerformanceMetrics, MediaAttentionMetrics
from src.models.canonical import MatchRecord, DeliveryRecord
from src.pipeline.entity_linker import EntityLinker
from src.storage.sqlite_manager import SQLiteStorageManager


@pytest.fixture
def temp_db(tmp_path: Path) -> SQLiteStorageManager:
    """Provides a fresh isolated SQLite database with full schema migrations."""
    db_file = tmp_path / "test_phase7.db"
    return SQLiteStorageManager(str(db_file))


def test_cricsheet_adapter_real_match_parsing():
    """Verifies that a genuine Cricsheet match file parses with valid score reconciliation."""
    match_file = Path("data/raw/cricsheet/1415755.json")
    assert match_file.exists(), "Cricsheet 1415755.json must exist in raw corpus"

    adapter = CricsheetAdapter()
    with open(match_file, "rb") as f:
        parsed = adapter.parse_json_bytes(f.read(), source_identifier="cricsheet_1415755")

    assert parsed.match.match_id == "cric_20240629_ind_sou"
    assert parsed.match.tournament == "ICC Men's T20 World Cup"
    assert parsed.match.winner_id == "IND"
    assert len(parsed.teams) == 2
    assert len(parsed.deliveries) == 251

    # Verify score reconciliation
    assert parsed.reconciliation.winner_reconciled is True
    assert parsed.reconciliation.innings_totals[1] == 176
    assert parsed.reconciliation.innings_totals[2] == 169


def test_ingestion_idempotency_on_isolated_db(temp_db: SQLiteStorageManager):
    """Verifies that running ingestion multiple times maintains exact record counts without duplicates."""
    match_file = Path("data/raw/cricsheet/1415755.json")
    adapter = CricsheetAdapter()

    with open(match_file, "rb") as f:
        raw_bytes = f.read()

    # Run 1
    parsed1 = adapter.parse_json_bytes(raw_bytes, source_identifier="cricsheet_1415755")
    temp_db.record_provenance(parsed1.provenance)
    for t in parsed1.teams:
        temp_db.upsert_team(t)
    for p in parsed1.players:
        temp_db.upsert_player(p)
    temp_db.upsert_match(parsed1.match)
    temp_db.replace_deliveries_for_match(parsed1.match.match_id, parsed1.deliveries)

    m_cnt_1 = temp_db.get_match_count()
    d_cnt_1 = temp_db.get_delivery_count()
    assert m_cnt_1 == 1
    assert d_cnt_1 == 251

    # Run 2 (Identical payload)
    parsed2 = adapter.parse_json_bytes(raw_bytes, source_identifier="cricsheet_1415755")
    temp_db.record_provenance(parsed2.provenance)
    for t in parsed2.teams:
        temp_db.upsert_team(t)
    for p in parsed2.players:
        temp_db.upsert_player(p)
    temp_db.upsert_match(parsed2.match)
    temp_db.replace_deliveries_for_match(parsed2.match.match_id, parsed2.deliveries)

    m_cnt_2 = temp_db.get_match_count()
    d_cnt_2 = temp_db.get_delivery_count()
    assert m_cnt_2 == 1, "Match count must not duplicate on re-ingestion"
    assert d_cnt_2 == 251, "Delivery count must not duplicate on re-ingestion"


def test_article_parsing_and_match_linking(temp_db: SQLiteStorageManager):
    """Verifies that genuine HTML news articles are parsed and linked to ground truth matches."""
    # First seed match
    match_file = Path("data/raw/cricsheet/1415755.json")
    cric_adapter = CricsheetAdapter()
    with open(match_file, "rb") as f:
        parsed = cric_adapter.parse_json_bytes(f.read())
    temp_db.record_provenance(parsed.provenance)
    for t in parsed.teams:
        temp_db.upsert_team(t)
    temp_db.upsert_match(parsed.match)

    # Parse article
    art_file = Path("data/raw/editorial/2024_Men's_T20_World_Cup_final.html")
    assert art_file.exists(), "Article file must exist"

    news_adapter = NewsArticleAdapter()
    with open(art_file, "rb") as f:
        art, paras, prov = news_adapter.parse_html(
            html_content=f.read(),
            canonical_url="https://en.wikipedia.org/wiki/2024_Men%27s_T20_World_Cup_final",
            source_domain="en.wikipedia.org",
        )

    assert len(paras) > 10
    assert len(art.full_text) > 500

    # Resolve match link
    linker = EntityLinker(storage=temp_db)
    cand = linker.resolve_match_link(art.headline, art.full_text)
    assert cand is not None
    assert cand.match_id == "cric_20240629_ind_sou"
    assert cand.confidence >= 0.65


def test_apdi_insufficient_data_safeguard():
    """Verifies that entities below evidence thresholds receive null APDI and INSUFFICIENT_DATA status."""
    apdi_calc = APDICalculator()

    # Single entity cohort (below min cohort size threshold of 3)
    p_metric = CricketPerformanceMetrics(
        metric_id="perf_test",
        entity_id="player_test",
        entity_name="Test Player",
        entity_type="player",
        role="batter",
        tournament="Test Tournament",
        matches_played=1,
        balls_faced=10,
        runs_scored=15,
        raw_performance_composite=15.0,
    )
    a_metric = MediaAttentionMetrics(
        metric_id="att_test",
        entity_id="player_test",
        entity_name="Test Player",
        entity_type="player",
        tournament="Test Tournament",
        paragraph_count=1,
        raw_mention_count=1,
    )

    records = apdi_calc.compute_cohort_apdi(
        role=CohortRole.BATTER,
        entities_data=[(a_metric, p_metric, None)],
        run_id="test_run",
        tournament="Test Tournament",
    )

    assert len(records) == 1
    rec = records[0]
    assert rec.evidence_sufficiency_status.value == "INSUFFICIENT_DATA"
    assert rec.apdi_value is None, "APDI value must be null when evidence is insufficient"
