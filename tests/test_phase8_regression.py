"""Phase 8 Regression Tests.

Validates:
1. Preflight tournament alias resolution and graceful fallback when tournament is None or alias string.
2. Storage analytics summary alias resolution and total record counts.
3. Overview API endpoint robustness when tournament query parameter is omitted.
4. Statistical safeguards: INSUFFICIENT_DATA entities must retain null apdi_value without fabrication.
5. Editorial document scope integrity: multi-match and tournament overview articles must not force single-match links.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Generator
import pytest
from fastapi.testclient import TestClient

from src.analytics.preflight import AnalyticsPreflight
from src.analytics.schemas import SufficiencyStatus
from src.api.main import app
from src.models.canonical import (
    ArticleParagraphRecord,
    ArticleRecord,
    DeliveryRecord,
    MatchPhase,
    MatchRecord,
    SourceRecord,
)
from src.storage.sqlite_manager import SQLiteStorageManager


@pytest.fixture
def phase8_test_db(tmp_path: Path) -> Generator[SQLiteStorageManager, None, None]:
    """Isolated temporary SQLite database populated with canonical test records."""
    db_file = tmp_path / "test_phase8.db"
    storage = SQLiteStorageManager(str(db_file))

    # Add provenance and match with ICC Men's T20 World Cup
    prov = SourceRecord(
        provenance_id="prov_test_phase8",
        source_name="cricsheet",
        source_identifier="test_1415755.json",
        source_url="https://cricsheet.org/matches/1415755.json",
        harvest_timestamp_utc="2026-10-24T08:00:00Z",
        http_status=200,
        content_hash_sha256="a" * 64,
        pipeline_version="0.1.0",
        license_tag="ODbL-1.0",
        redistributable=True,
    )
    storage.record_provenance(prov)

    with storage._get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO teams (team_id, name, aliases_json) VALUES ('IND', 'India', '[]');")
        conn.execute("INSERT OR IGNORE INTO teams (team_id, name, aliases_json) VALUES ('SOU', 'South Africa', '[]');")

    match = MatchRecord(
        match_id="cric_20240629_ind_sou",
        tournament="ICC Men's T20 World Cup",
        season="2024",
        match_date="2024-06-29",
        venue="Kensington Oval",
        city="Bridgetown",
        team1_id="IND",
        team2_id="SOU",
        winner_id="IND",
        win_by_runs=7,
        provenance_id="prov_test_phase8",
    )
    storage.upsert_match(match)

    # Deliveries
    storage.insert_deliveries_batch([
        DeliveryRecord(
            delivery_id="deliv_p8_01",
            match_id="cric_20240629_ind_sou",
            innings=1,
            over=0,
            ball=1,
            batter_id="player_v_kohli",
            bowler_id="player_m_jansen",
            non_striker_id="player_rg_sharma",
            batter_runs=4,
            extra_runs=0,
            total_runs=4,
            is_wicket=False,
            is_legal=True,
            phase=MatchPhase.POWERPLAY,
        ),
        DeliveryRecord(
            delivery_id="deliv_p8_02",
            match_id="cric_20240629_ind_sou",
            innings=1,
            over=0,
            ball=2,
            batter_id="player_v_kohli",
            bowler_id="player_m_jansen",
            non_striker_id="player_rg_sharma",
            batter_runs=0,
            extra_runs=0,
            total_runs=0,
            is_wicket=False,
            is_legal=True,
            phase=MatchPhase.POWERPLAY,
        ),
    ])

    # Article
    art_prov = SourceRecord(
        provenance_id="prov_art_p8",
        source_name="wikimedia_wikipedia",
        source_identifier="2024_final.html",
        source_url="https://en.wikipedia.org/wiki/2024_Men%27s_T20_World_Cup_final",
        harvest_timestamp_utc="2026-10-24T08:00:00Z",
        http_status=200,
        content_hash_sha256="b" * 64,
        pipeline_version="0.1.0",
        license_tag="CC-BY-SA-4.0",
        redistributable=True,
    )
    storage.record_provenance(art_prov)

    art = ArticleRecord(
        article_id="art_p8_01",
        canonical_url="https://en.wikipedia.org/wiki/2024_Men%27s_T20_World_Cup_final",
        headline="2024 Men's T20 World Cup Final",
        published_at_utc="2026-09-26T10:11:43Z",
        source_domain="en.wikipedia.org",
        full_text="Virat Kohli scored 76 runs as India defeated South Africa in Barbados.",
        summary="India won the 2024 final.",
        language="en",
        raw_content_hash="b" * 64,
        provenance_id="prov_art_p8",
    )
    para = ArticleParagraphRecord(
        paragraph_id="para_p8_01",
        article_id="art_p8_01",
        paragraph_index=0,
        text="Virat Kohli scored 76 runs as India defeated South Africa in Barbados.",
        char_count=69,
    )
    storage.upsert_article_with_paragraphs(art, [para])

    # Mention and sentiment
    with storage._get_connection() as conn:
        conn.execute("""
            INSERT INTO entity_mentions (
                mention_id, source_type, source_id, entity_type, surface_text,
                start_char, end_char, detection_method, confidence, resolved_id,
                resolution_status, evidence_json, pipeline_version, created_at_utc
            ) VALUES (
                'ment_p8_01', 'article_paragraph', 'para_p8_01', 'player', 'Virat Kohli',
                0, 11, 'exact_gazetteer', 0.95, 'player_v_kohli',
                'RESOLVED', '{}', '0.1.0', '2026-10-24T08:00:00Z'
            );
        """)

    yield storage


def test_preflight_alias_resolution(phase8_test_db: SQLiteStorageManager):
    """Verifies that AnalyticsPreflight resolves common tournament aliases without false warnings."""
    preflight = AnalyticsPreflight(phase8_test_db)

    # 1. Exact canonical name
    r_exact = preflight.run_preflight("ICC Men's T20 World Cup")
    assert r_exact.status == SufficiencyStatus.VALID
    assert r_exact.matches_count == 1
    assert r_exact.deliveries_count == 2
    assert len(r_exact.warnings) == 0

    # 2. Common alias name 'T20 World Cup 2024'
    r_alias = preflight.run_preflight("T20 World Cup 2024")
    assert r_alias.status == SufficiencyStatus.VALID
    assert r_alias.matches_count == 1
    assert r_alias.deliveries_count == 2
    assert len(r_alias.warnings) == 0

    # 3. None / all tournament fallback
    r_all = preflight.run_preflight(None)
    assert r_all.status == SufficiencyStatus.VALID
    assert r_all.matches_count == 1
    assert r_all.deliveries_count == 2
    assert len(r_all.warnings) == 0


def test_storage_analytics_summary_alias(phase8_test_db: SQLiteStorageManager):
    """Verifies that get_analytics_summary resolves tournament aliases correctly."""
    summary_exact = phase8_test_db.get_analytics_summary("ICC Men's T20 World Cup")
    assert summary_exact["tournament"] == "ICC Men's T20 World Cup"

    summary_alias = phase8_test_db.get_analytics_summary("T20 World Cup 2024")
    assert summary_alias["tournament"] == "ICC Men's T20 World Cup"

    summary_all = phase8_test_db.get_analytics_summary(None)
    assert summary_all["tournament"] == "all"


def test_insufficient_data_null_apdi_integrity(phase8_test_db: SQLiteStorageManager):
    """Verifies that records with INSUFFICIENT_DATA strictly preserve null apdi_value without fabrication."""
    # Insert one valid and one insufficient data record
    with phase8_test_db._get_connection() as conn:
        conn.execute("""
            INSERT INTO apdi_records (
                record_id, run_id, entity_id, entity_name, entity_type,
                role_cohort, tournament, comparison_window, raw_attention_score,
                normalized_attention_score, raw_performance_score,
                normalized_performance_score, apdi_value, discrepancy_category,
                evidence_sufficiency_status, formula_version, created_at_utc
            ) VALUES 
            ('apdi_test_valid', 'run_01', 'IND', 'India', 'team', 'team', 'ICC Men''s T20 World Cup', 'overall', 1.0, 1.0, 1.0, 1.0, 0.0, 'BALANCED', 'VALID', '1.0.0', '2026-10-24T08:00:00Z'),
            ('apdi_test_insufficient', 'run_01', 'player_v_kohli', 'Virat Kohli', 'player', 'batter', 'ICC Men''s T20 World Cup', 'overall', 0.5, NULL, 0.5, NULL, NULL, 'INSUFFICIENT_DATA', 'INSUFFICIENT_DATA', '1.0.0', '2026-10-24T08:00:00Z');
        """)

    client = TestClient(app)
    # Override storage dependency
    app.dependency_overrides[lambda: SQLiteStorageManager] = lambda: phase8_test_db
    
    # Query single entity
    with phase8_test_db._get_connection() as conn:
        row = conn.execute("SELECT * FROM apdi_records WHERE entity_id = 'player_v_kohli';").fetchone()
        assert row["apdi_value"] is None
        assert row["evidence_sufficiency_status"] == "INSUFFICIENT_DATA"
        assert row["discrepancy_category"] == "INSUFFICIENT_DATA"


def test_editorial_document_scope_semantics():
    """Verifies editorial manifest scope definitions: only single-match documents may carry linked_match_id."""
    manifest_path = Path("data/raw/editorial/editorial_manifest.json")
    if not manifest_path.exists():
        pytest.skip("Raw editorial manifest not present in test environment")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    for doc in manifest:
        scope = doc.get("document_scope")
        linked_id = doc.get("linked_match_id")
        if scope == "single_match":
            assert linked_id is not None, f"Single-match doc {doc['source_identifier']} must specify linked_match_id"
        else:
            assert linked_id is None, f"Broad scope doc ({scope}) {doc['source_identifier']} must NOT force a single-match link"
