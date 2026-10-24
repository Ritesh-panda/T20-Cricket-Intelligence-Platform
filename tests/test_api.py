"""Comprehensive Integration and Unit Tests for Phase 6B FastAPI Research API.

Tests:
1. Application startup, liveness, and database readiness probes.
2. System status endpoint with preflight data sufficiency status.
3. Strict empty database behavior across all list and detail endpoints.
4. Nonexistent resource handling with standardized 404 ErrorResponse.
5. Parameter validation and pagination limits (422 responses).
6. SQL injection resistance via parameterized filtering.
7. Populated database behavior for matches, deliveries, and match performance scorecard.
8. Canonical players and teams retrieval with alias search.
9. Articles, paragraphs, and ball-by-ball commentary retrieval with source attribution.
10. Topics, entity mentions, timeline snapshots, and cross-source alignments.
11. Media attention, cricket performance, entity framing, and APDI analytics.
12. APDI status preservation: INSUFFICIENT_DATA retains null numerical score.
13. Structural analytics validation endpoint.
14. Provenance and observability endpoints without leaking secrets or credentials.
15. CORS policy headers and preflight handling.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator
import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import get_storage
from src.api.main import create_app
from src.storage.sqlite_manager import SQLiteStorageManager


@pytest.fixture
def temp_storage(tmp_path: Path) -> SQLiteStorageManager:
    """Provides isolated, temporary SQLite database instance."""
    db_file = tmp_path / "test_api_isolated.db"
    return SQLiteStorageManager(db_file)


@pytest.fixture
def empty_client(temp_storage: SQLiteStorageManager) -> Generator[TestClient, None, None]:
    """Test client bound to an empty temporary SQLite database."""
    app = create_app()
    app.dependency_overrides[get_storage] = lambda: temp_storage
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def populated_storage(tmp_path: Path) -> SQLiteStorageManager:
    """Provides a temporary SQLite database populated with controlled synthetic records."""
    db_file = tmp_path / "test_api_populated.db"
    storage = SQLiteStorageManager(db_file)
    now_iso = datetime.now(timezone.utc).isoformat()

    with storage._get_connection() as conn:
        # 1. Source record
        conn.execute(
            """
            INSERT INTO source_records (
                provenance_id, source_name, source_identifier, source_url,
                harvest_timestamp_utc, http_status, content_hash_sha256,
                pipeline_version, license_tag, redistributable
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                "prov_cricsheet_001",
                "cricsheet",
                "match_1423161",
                "https://cricsheet.org/matches/1423161",
                now_iso,
                200,
                "sha256_mock_hash_1",
                "6B.1.0",
                "CC-BY-4.0",
                1,
            ),
        )

        # 2. Teams
        conn.execute(
            "INSERT INTO teams (team_id, name, aliases_json) VALUES (?, ?, ?);",
            ("team_ind", "India", json.dumps(["IND", "Men in Blue"])),
        )
        conn.execute(
            "INSERT INTO teams (team_id, name, aliases_json) VALUES (?, ?, ?);",
            ("team_sa", "South Africa", json.dumps(["SA", "Proteas"])),
        )

        # 3. Players
        conn.execute(
            """
            INSERT INTO players (
                player_id, full_name, cricsheet_id, primary_team_id,
                batting_style, bowling_style, aliases_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                "p_kohli",
                "Virat Kohli",
                "cric_vk_01",
                "team_ind",
                "Right-hand bat",
                "Right-arm medium",
                json.dumps(["King Kohli", "V Kohli"]),
            ),
        )
        conn.execute(
            """
            INSERT INTO players (
                player_id, full_name, cricsheet_id, primary_team_id,
                batting_style, bowling_style, aliases_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                "p_bumrah",
                "Jasprit Bumrah",
                "cric_jb_01",
                "team_ind",
                "Right-hand bat",
                "Right-arm fast",
                json.dumps(["Boom Boom", "J Bumrah"]),
            ),
        )
        conn.execute(
            """
            INSERT INTO players (
                player_id, full_name, cricsheet_id, primary_team_id,
                batting_style, bowling_style, aliases_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                "p_klaasen",
                "Heinrich Klaasen",
                "cric_hk_01",
                "team_sa",
                "Right-hand bat",
                "Right-arm offbreak",
                json.dumps(["H Klaasen"]),
            ),
        )

        # 4. Match
        conn.execute(
            """
            INSERT INTO matches (
                match_id, tournament, season, match_date, venue, city,
                team1_id, team2_id, toss_winner_id, toss_decision, winner_id,
                win_by_runs, win_by_wickets, player_of_match_id, target_runs,
                metadata_json, provenance_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                "m_final_2024",
                "T20 World Cup 2024",
                "2024",
                "2024-06-29",
                "Kensington Oval",
                "Bridgetown",
                "team_ind",
                "team_sa",
                "team_ind",
                "bat",
                "team_ind",
                7,
                None,
                "p_kohli",
                177,
                json.dumps({"stage": "Final", "attendance": 28000}),
                "prov_cricsheet_001",
            ),
        )

        # 5. Deliveries
        conn.execute(
            """
            INSERT INTO deliveries (
                delivery_id, match_id, innings, over_num, ball_num,
                batter_id, bowler_id, non_striker_id, batter_runs, extra_runs,
                extra_type, total_runs, is_legal, is_wicket, wicket_kind,
                player_dismissed_id, phase
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                "del_001",
                "m_final_2024",
                1,
                0,
                1,
                "p_kohli",
                "p_klaasen",
                "p_bumrah",
                4,
                0,
                None,
                4,
                1,
                0,
                None,
                None,
                "powerplay",
            ),
        )
        conn.execute(
            """
            INSERT INTO deliveries (
                delivery_id, match_id, innings, over_num, ball_num,
                batter_id, bowler_id, non_striker_id, batter_runs, extra_runs,
                extra_type, total_runs, is_legal, is_wicket, wicket_kind,
                player_dismissed_id, phase
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                "del_002",
                "m_final_2024",
                1,
                0,
                2,
                "p_kohli",
                "p_klaasen",
                "p_bumrah",
                6,
                0,
                None,
                6,
                1,
                0,
                None,
                None,
                "powerplay",
            ),
        )
        conn.execute(
            """
            INSERT INTO deliveries (
                delivery_id, match_id, innings, over_num, ball_num,
                batter_id, bowler_id, non_striker_id, batter_runs, extra_runs,
                extra_type, total_runs, is_legal, is_wicket, wicket_kind,
                player_dismissed_id, phase
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                "del_003",
                "m_final_2024",
                2,
                15,
                1,
                "p_klaasen",
                "p_bumrah",
                None,
                0,
                0,
                None,
                0,
                1,
                1,
                "bowled",
                "p_klaasen",
                "death",
            ),
        )

        # 6. Articles & Paragraphs
        conn.execute(
            """
            INSERT INTO articles (
                article_id, canonical_url, headline, author, published_at_utc,
                source_domain, full_text, summary, language, raw_content_hash, provenance_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                "art_001",
                "https://espncricinfo.com/story/india-win-t20-wc",
                "India clinch T20 World Cup thrilling final",
                "Andrew Fidel Fernando",
                "2024-06-29T21:00:00Z",
                "espncricinfo.com",
                "Virat Kohli played an anchor innings while Jasprit Bumrah held nerve in death overs.",
                "India wins T20 World Cup.",
                "en",
                "hash_art_001",
                "prov_cricsheet_001",
            ),
        )
        conn.execute(
            """
            INSERT INTO article_paragraphs (
                paragraph_id, article_id, paragraph_index, text, char_count
            ) VALUES (?, ?, ?, ?, ?);
            """,
            (
                "para_001",
                "art_001",
                0,
                "Virat Kohli played an anchor innings while Jasprit Bumrah held nerve.",
                68,
            ),
        )

        # 7. Commentary
        conn.execute(
            """
            INSERT INTO commentary_entries (
                commentary_id, match_id, innings, over_num, ball_num,
                bowler_raw, batter_raw, text, event_tags_json, source_domain,
                harvest_timestamp_utc, provenance_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                "comm_001",
                "m_final_2024",
                2,
                15,
                1,
                "Bumrah",
                "Klaasen",
                "OUT! Clean bowled! Bumrah cuts Klaasen in half with an unplayable cutter!",
                json.dumps(["wicket", "bowled"]),
                "cricbuzz.com",
                now_iso,
                "prov_cricsheet_001",
            ),
        )

        # 8. Topics
        conn.execute(
            """
            INSERT INTO topic_runs (
                run_id, corpus_type, algorithm, n_clusters_requested,
                n_clusters_found, n_noise_points, parameters_json, created_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            ("topic_run_01", "articles", "kmeans", 3, 3, 0, json.dumps({"k": 3}), now_iso),
        )
        conn.execute(
            """
            INSERT INTO topic_clusters (
                cluster_id, run_id, cluster_index, topic_label, keywords_json,
                doc_count, representative_doc_ids_json, intra_cluster_similarity, is_noise
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                "topic_c1",
                "topic_run_01",
                0,
                "Death Bowling & Defense",
                json.dumps(["bumrah", "death", "cutter", "wicket"]),
                12,
                json.dumps(["para_001"]),
                0.84,
                0,
            ),
        )

        # 9. Entity mentions
        conn.execute(
            """
            INSERT INTO entity_mentions (
                mention_id, source_type, source_id, entity_type, surface_text,
                start_char, end_char, detection_method, confidence, resolved_id,
                resolution_status, evidence_json, pipeline_version, created_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                "men_001",
                "article_paragraph",
                "para_001",
                "PLAYER",
                "Virat Kohli",
                0,
                11,
                "gazetteer_exact",
                1.0,
                "p_kohli",
                "RESOLVED",
                json.dumps({"match": "direct"}),
                "4.0.0",
                now_iso,
            ),
        )

        # 10. Timeline & Cross-source matches
        conn.execute(
            """
            INSERT INTO timeline_snapshots (
                snapshot_id, bucket_label, doc_count, mean_sentiment,
                sentiment_distribution_json, top_topics_json, top_entities_json,
                match_events_count, observed_timestamps_count, inferred_timestamps_count, created_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                "snap_001",
                "2024-06-29T21:00:00Z",
                5,
                0.75,
                json.dumps({"POSITIVE": 4, "NEUTRAL": 1, "NEGATIVE": 0}),
                json.dumps(["Final Victory"]),
                json.dumps(["p_kohli", "p_bumrah"]),
                3,
                5,
                0,
                now_iso,
            ),
        )
        conn.execute(
            """
            INSERT INTO cross_source_matches (
                match_link_id, editorial_norm_id, editorial_source_id,
                commentary_norm_id, commentary_source_id, match_id,
                similarity_score, status, confidence, matching_method,
                evidence_json, created_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                "xmatch_001",
                "norm_ed_01",
                "para_001",
                "norm_comm_01",
                "comm_001",
                "m_final_2024",
                0.91,
                "ALIGNED",
                0.89,
                "embedding_cosine",
                json.dumps({"token_overlap": 0.65}),
                now_iso,
            ),
        )

        # 11. Attention & Performance Analytics
        conn.execute(
            """
            INSERT INTO attention_metrics (
                metric_id, entity_id, entity_name, entity_type, tournament,
                window_start, window_end, paragraph_count, raw_mention_count,
                article_reach, source_diversity_count, sources_json, prominence_score,
                headline_mentions, lead_paragraph_mentions, body_paragraph_mentions,
                event_linked_mentions, temporal_distribution_json, article_ids_json,
                paragraph_ids_json, raw_attention_composite, formula_version, created_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                "att_p_kohli",
                "p_kohli",
                "Virat Kohli",
                "player",
                "T20 World Cup 2024",
                "2024-06-01",
                "2024-06-29",
                15,
                22,
                8,
                3,
                json.dumps(["espncricinfo.com", "cricbuzz.com"]),
                0.88,
                3,
                5,
                7,
                4,
                json.dumps({"2024-06-29": 15}),
                json.dumps(["art_001"]),
                json.dumps(["para_001"]),
                82.5,
                "6A.1.0",
                now_iso,
            ),
        )
        conn.execute(
            """
            INSERT INTO performance_metrics (
                metric_id, entity_id, entity_name, entity_type, role, tournament,
                window_start, window_end, matches_played, innings_count, runs_scored,
                balls_faced, strike_rate, fours, sixes, dismissals, batting_average,
                legal_balls_bowled, overs_bowled, runs_conceded, wickets_taken,
                bowling_economy, bowling_average, bowling_strike_rate, wides_conceded,
                noballs_conceded, powerplay_runs, powerplay_balls, powerplay_wickets,
                death_runs, death_balls, death_wickets, team_wins, team_matches,
                win_percentage, raw_performance_composite, match_ids_json, raw_stats_json,
                formula_version, created_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                "perf_p_kohli",
                "p_kohli",
                "Virat Kohli",
                "player",
                "batter",
                "T20 World Cup 2024",
                "2024-06-01",
                "2024-06-29",
                8,
                8,
                151,
                135,
                111.85,
                14,
                3,
                8,
                18.87,
                0,
                0.0,
                0,
                0,
                None,
                None,
                None,
                0,
                0,
                50,
                45,
                0,
                25,
                18,
                0,
                8,
                8,
                100.0,
                55.4,
                json.dumps(["m_final_2024"]),
                json.dumps({"runs": 151}),
                "6A.1.0",
                now_iso,
            ),
        )

        # 12. APDI Records
        conn.execute(
            """
            INSERT INTO apdi_records (
                record_id, run_id, entity_id, entity_name, entity_type,
                role_cohort, tournament, comparison_window, raw_attention_score,
                normalized_attention_score, raw_performance_score, normalized_performance_score,
                apdi_value, discrepancy_category, evidence_sufficiency_status,
                sample_size_indicators_json, data_quality_warnings_json, framing_breakdown_json,
                evidence_lineage_json, formula_version, created_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                "apdi_p_kohli",
                "arun_001",
                "p_kohli",
                "Virat Kohli",
                "player",
                "batter",
                "T20 World Cup 2024",
                "tournament",
                82.5,
                0.85,
                55.4,
                0.60,
                0.25,
                "OVER_ATTENDED",
                "VALID",
                json.dumps({"matches_played": 8, "paragraphs": 15}),
                json.dumps([]),
                json.dumps({"positive": 10, "neutral": 3, "negative": 2}),
                json.dumps({"mention_count": 22}),
                "6A.1.0",
                now_iso,
            ),
        )

        # 13. APDI with INSUFFICIENT_DATA (preserves null apdi_value)
        conn.execute(
            """
            INSERT INTO apdi_records (
                record_id, run_id, entity_id, entity_name, entity_type,
                role_cohort, tournament, comparison_window, raw_attention_score,
                normalized_attention_score, raw_performance_score, normalized_performance_score,
                apdi_value, discrepancy_category, evidence_sufficiency_status,
                sample_size_indicators_json, data_quality_warnings_json, framing_breakdown_json,
                evidence_lineage_json, formula_version, created_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                "apdi_p_bumrah",
                "arun_001",
                "p_bumrah",
                "Jasprit Bumrah",
                "player",
                "bowler",
                "T20 World Cup 2024",
                "tournament",
                12.0,
                None,
                88.0,
                None,
                None,
                "INSUFFICIENT_DATA",
                "INSUFFICIENT_DATA",
                json.dumps({"matches_played": 1, "paragraphs": 1}),
                json.dumps(["Sample size below threshold"]),
                json.dumps({}),
                json.dumps({}),
                "6A.1.0",
                now_iso,
            ),
        )

        # 14. Ingestion Runs & Analytics Runs
        conn.execute(
            """
            INSERT INTO ingestion_runs (
                run_id, source_name, status, started_at_utc, completed_at_utc,
                records_extracted, records_ingested, records_skipped, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            ("irun_001", "cricsheet", "COMPLETED", now_iso, now_iso, 55, 55, 0, None),
        )
        conn.execute(
            """
            INSERT INTO analytics_runs (
                run_id, status, tournament, entity_type, cohorts_analyzed_json,
                entities_processed, valid_apdi_count, insufficient_data_count,
                warnings_json, started_at_utc, completed_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                "arun_001",
                "COMPLETED",
                "T20 World Cup 2024",
                "player",
                json.dumps(["batter", "bowler"]),
                2,
                1,
                1,
                json.dumps([]),
                now_iso,
                now_iso,
            ),
        )

    return storage


@pytest.fixture
def populated_client(populated_storage: SQLiteStorageManager) -> Generator[TestClient, None, None]:
    """Test client bound to populated temporary database."""
    app = create_app()
    app.dependency_overrides[get_storage] = lambda: populated_storage
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


# =============================================================================
# 1. Health, Readiness, and System Status Tests
# =============================================================================
def test_health_liveness_endpoint(empty_client: TestClient):
    res = empty_client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert "timestamp_utc" in data


def test_ready_persistence_probe(empty_client: TestClient):
    res = empty_client.get("/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert data["database_accessible"] is True
    assert data["schema_version"] == 5
    assert data["database_tables_count"] >= 20


def test_status_endpoint_reports_insufficient_data(empty_client: TestClient):
    res = empty_client.get("/api/v1/status")
    assert res.status_code == 200
    data = res.json()
    assert data["pipeline_status"] == "empty"
    assert data["data_sufficiency_status"] == "INSUFFICIENT_DATA"
    assert data["is_analytics_ready"] is False
    assert len(data["warnings"]) > 0
    assert "canonical_schemas" in data["supported_capabilities"]


# =============================================================================
# 2. Empty Database Invariant Tests
# =============================================================================
def test_empty_database_returns_valid_collections(empty_client: TestClient):
    endpoints = [
        "/api/v1/matches",
        "/api/v1/players",
        "/api/v1/teams",
        "/api/v1/articles",
        "/api/v1/commentary",
        "/api/v1/topics",
        "/api/v1/entities",
        "/api/v1/narratives/timeline",
        "/api/v1/narratives/matches",
        "/api/v1/analytics/attention",
        "/api/v1/analytics/performance",
        "/api/v1/analytics/apdi",
        "/api/v1/observability/ingestion-runs",
        "/api/v1/observability/sources",
        "/api/v1/observability/analytics-runs",
    ]
    for endpoint in endpoints:
        res = empty_client.get(endpoint)
        assert res.status_code == 200, f"Failed on {endpoint}"
        body = res.json()
        assert body["items"] == [], f"Expected empty items on {endpoint}"
        assert body["pagination"]["total"] == 0
        assert body["pagination"]["has_more"] is False


def test_empty_analytics_overview_state(empty_client: TestClient):
    res = empty_client.get("/api/v1/analytics/overview")
    assert res.status_code == 200
    data = res.json()
    assert data["apdi_records_count"] == 0
    assert data["preflight_status"] == "INSUFFICIENT_DATA"
    assert data["is_eligible"] is False


def test_empty_framing_returns_zero_scores(empty_client: TestClient):
    res = empty_client.get("/api/v1/analytics/framing?entity_id=p_unknown")
    assert res.status_code == 200
    data = res.json()
    assert data["entity_id"] == "p_unknown"
    assert data["positive_count"] == 0
    assert data["neutral_count"] == 0
    assert data["negative_count"] == 0
    assert data["net_framing_score"] == 0.0


# =============================================================================
# 3. Nonexistent Resource 404 Tests
# =============================================================================
def test_nonexistent_individual_resources_return_404(empty_client: TestClient):
    not_found_endpoints = [
        "/api/v1/matches/m_missing",
        "/api/v1/matches/m_missing/deliveries",
        "/api/v1/matches/m_missing/performance",
        "/api/v1/players/p_missing",
        "/api/v1/teams/t_missing",
        "/api/v1/articles/art_missing",
        "/api/v1/articles/art_missing/paragraphs",
        "/api/v1/commentary/comm_missing",
        "/api/v1/topics/top_missing",
        "/api/v1/analytics/apdi/p_missing",
    ]
    for endpoint in not_found_endpoints:
        res = empty_client.get(endpoint)
        assert res.status_code == 404, f"Expected 404 on {endpoint}, got {res.status_code}"
        data = res.json()
        assert data["error"] == "ResourceNotFound"
        assert "not found" in data["message"].lower()


# =============================================================================
# 4. Parameter Validation & SQL Injection Resistance
# =============================================================================
def test_pagination_boundary_validation(empty_client: TestClient):
    # Limit too large
    res = empty_client.get("/api/v1/matches?limit=101")
    assert res.status_code == 422
    assert res.json()["error"] == "ValidationError"

    # Limit below 1
    res = empty_client.get("/api/v1/matches?limit=0")
    assert res.status_code == 422

    # Negative offset
    res = empty_client.get("/api/v1/matches?offset=-1")
    assert res.status_code == 422


def test_sql_injection_resistance_in_filters(empty_client: TestClient):
    malicious = "'; DROP TABLE matches; --"
    res = empty_client.get(f"/api/v1/matches?tournament={malicious}")
    assert res.status_code == 200
    assert res.json()["items"] == []

    # Verify table matches still exists
    res_ready = empty_client.get("/ready")
    assert res_ready.status_code == 200
    assert res_ready.json()["database_accessible"] is True


# =============================================================================
# 5. Populated Match and Performance Scorecard Tests
# =============================================================================
def test_populated_matches_and_scorecard(populated_client: TestClient):
    # List matches
    res = populated_client.get("/api/v1/matches?tournament=T20 World Cup 2024")
    assert res.status_code == 200
    data = res.json()
    assert data["pagination"]["total"] == 1
    match = data["items"][0]
    assert match["match_id"] == "m_final_2024"
    assert match["venue"] == "Kensington Oval"

    # Single match
    res_single = populated_client.get("/api/v1/matches/m_final_2024")
    assert res_single.status_code == 200
    assert res_single.json()["winner_id"] == "team_ind"

    # Deliveries
    res_deliv = populated_client.get("/api/v1/matches/m_final_2024/deliveries")
    assert res_deliv.status_code == 200
    assert res_deliv.json()["pagination"]["total"] == 3

    # Deliveries filtered by phase
    res_pp = populated_client.get("/api/v1/matches/m_final_2024/deliveries?phase=powerplay")
    assert res_pp.status_code == 200
    assert res_pp.json()["pagination"]["total"] == 2

    # Match scorecard calculation
    res_perf = populated_client.get("/api/v1/matches/m_final_2024/performance")
    assert res_perf.status_code == 200
    scorecard = res_perf.json()
    assert scorecard["match_id"] == "m_final_2024"
    assert len(scorecard["batters"]) >= 1

    kohli = next((b for b in scorecard["batters"] if b["player_id"] == "p_kohli"), None)
    assert kohli is not None
    assert kohli["runs"] == 10  # 4 + 6
    assert kohli["balls"] == 2
    assert kohli["fours"] == 1
    assert kohli["sixes"] == 1
    assert kohli["strike_rate"] == 500.0


# =============================================================================
# 6. Canonical Players and Teams Tests
# =============================================================================
def test_players_and_teams_retrieval(populated_client: TestClient):
    # List players
    res_p = populated_client.get("/api/v1/players")
    assert res_p.status_code == 200
    assert res_p.json()["pagination"]["total"] == 3

    # Search player by alias
    res_search = populated_client.get("/api/v1/players?search=King")
    assert res_search.status_code == 200
    assert res_search.json()["pagination"]["total"] == 1
    assert res_search.json()["items"][0]["player_id"] == "p_kohli"

    # Single player
    res_single = populated_client.get("/api/v1/players/p_bumrah")
    assert res_single.status_code == 200
    assert res_single.json()["bowling_style"] == "Right-arm fast"

    # Teams list & search
    res_teams = populated_client.get("/api/v1/teams?search=Proteas")
    assert res_teams.status_code == 200
    assert res_teams.json()["pagination"]["total"] == 1
    assert res_teams.json()["items"][0]["team_id"] == "team_sa"


# =============================================================================
# 7. Articles and Commentary Tests
# =============================================================================
def test_articles_and_commentary_retrieval(populated_client: TestClient):
    # Articles
    res_art = populated_client.get("/api/v1/articles?source_domain=espncricinfo.com")
    assert res_art.status_code == 200
    assert res_art.json()["pagination"]["total"] == 1
    art = res_art.json()["items"][0]
    assert "India clinch" in art["headline"]

    # Article detail (includes full_text)
    res_detail = populated_client.get(f"/api/v1/articles/{art['article_id']}")
    assert res_detail.status_code == 200
    assert "Virat Kohli played" in res_detail.json()["full_text"]

    # Paragraphs
    res_para = populated_client.get(f"/api/v1/articles/{art['article_id']}/paragraphs")
    assert res_para.status_code == 200
    assert res_para.json()["pagination"]["total"] == 1

    # Commentary
    res_comm = populated_client.get("/api/v1/commentary?match_id=m_final_2024")
    assert res_comm.status_code == 200
    assert res_comm.json()["pagination"]["total"] == 1
    comm = res_comm.json()["items"][0]
    assert comm["bowler_raw"] == "Bumrah"
    assert "wicket" in comm["event_tags"]


# =============================================================================
# 8. Topics and Narrative Intelligence Tests
# =============================================================================
def test_nlp_and_narrative_intelligence(populated_client: TestClient):
    # Topics
    res_top = populated_client.get("/api/v1/topics")
    assert res_top.status_code == 200
    assert res_top.json()["pagination"]["total"] == 1
    topic = res_top.json()["items"][0]
    assert topic["topic_label"] == "Death Bowling & Defense"
    assert "bumrah" in topic["keywords"]

    # Single topic
    res_single_top = populated_client.get("/api/v1/topics/topic_c1")
    assert res_single_top.status_code == 200
    assert res_single_top.json()["doc_count"] == 12

    # Entity mentions
    res_mentions = populated_client.get("/api/v1/entities?resolution_status=RESOLVED")
    assert res_mentions.status_code == 200
    assert res_mentions.json()["pagination"]["total"] == 1
    assert res_mentions.json()["items"][0]["resolved_id"] == "p_kohli"

    # Timeline snapshots
    res_time = populated_client.get("/api/v1/narratives/timeline")
    assert res_time.status_code == 200
    assert res_time.json()["pagination"]["total"] == 1
    assert res_time.json()["items"][0]["mean_sentiment"] == 0.75

    # Cross-source matches
    res_xmatch = populated_client.get("/api/v1/narratives/matches?status=ALIGNED")
    assert res_xmatch.status_code == 200
    assert res_xmatch.json()["pagination"]["total"] == 1
    assert res_xmatch.json()["items"][0]["similarity_score"] == 0.91


# =============================================================================
# 9. Analytics, Framing, and APDI Tests
# =============================================================================
def test_analytics_and_apdi_retrieval(populated_client: TestClient):
    # Overview
    res_ov = populated_client.get("/api/v1/analytics/overview")
    assert res_ov.status_code == 200
    overview = res_ov.json()
    assert overview["attention_metrics_count"] == 1
    assert overview["performance_metrics_count"] == 1
    assert overview["apdi_records_count"] == 2
    assert overview["over_attended_count"] == 1
    assert overview["insufficient_data_count"] == 1

    # Attention metrics
    res_att = populated_client.get("/api/v1/analytics/attention?entity_id=p_kohli")
    assert res_att.status_code == 200
    assert res_att.json()["pagination"]["total"] == 1
    assert res_att.json()["items"][0]["raw_attention_composite"] == 82.5

    # Performance metrics
    res_perf = populated_client.get("/api/v1/analytics/performance?role=batter")
    assert res_perf.status_code == 200
    assert res_perf.json()["pagination"]["total"] == 1
    assert res_perf.json()["items"][0]["runs_scored"] == 151

    # Framing metrics
    res_frame = populated_client.get("/api/v1/analytics/framing?entity_id=p_kohli")
    assert res_frame.status_code == 200
    assert res_frame.json()["entity_id"] == "p_kohli"

    # APDI listing
    res_apdi = populated_client.get("/api/v1/analytics/apdi")
    assert res_apdi.status_code == 200
    assert res_apdi.json()["pagination"]["total"] == 2

    # Single APDI record
    res_single_apdi = populated_client.get("/api/v1/analytics/apdi/p_kohli")
    assert res_single_apdi.status_code == 200
    apdi_rec = res_single_apdi.json()
    assert apdi_rec["discrepancy_category"] == "OVER_ATTENDED"
    assert apdi_rec["apdi_value"] == 0.25

    # APDI missing-data invariant: INSUFFICIENT_DATA retains null numerical score
    res_insufficient = populated_client.get("/api/v1/analytics/apdi/p_bumrah")
    assert res_insufficient.status_code == 200
    ins_rec = res_insufficient.json()
    assert ins_rec["discrepancy_category"] == "INSUFFICIENT_DATA"
    assert ins_rec["apdi_value"] is None
    assert ins_rec["normalized_attention_score"] is None
    assert ins_rec["normalized_performance_score"] is None

    # Validation endpoint
    res_val = populated_client.get("/api/v1/analytics/validation")
    assert res_val.status_code == 200
    assert res_val.json()["is_valid"] is True
    assert res_val.json()["issues"] == []


# =============================================================================
# 10. Observability and Provenance Tests
# =============================================================================
def test_observability_endpoints(populated_client: TestClient):
    # Ingestion runs
    res_iruns = populated_client.get("/api/v1/observability/ingestion-runs?status=COMPLETED")
    assert res_iruns.status_code == 200
    assert res_iruns.json()["pagination"]["total"] == 1
    assert res_iruns.json()["items"][0]["records_ingested"] == 55

    # Sources provenance
    res_src = populated_client.get("/api/v1/observability/sources")
    assert res_src.status_code == 200
    assert res_src.json()["pagination"]["total"] == 1
    source = res_src.json()["items"][0]
    assert source["license_tag"] == "CC-BY-4.0"
    assert "password" not in str(source).lower()
    assert "secret" not in str(source).lower()

    # Pipeline stats
    res_stats = populated_client.get("/api/v1/observability/pipeline-stats")
    assert res_stats.status_code == 200
    assert "state_distribution" in res_stats.json()

    # Analytics runs
    res_aruns = populated_client.get("/api/v1/observability/analytics-runs")
    assert res_aruns.status_code == 200
    assert res_aruns.json()["pagination"]["total"] == 1
    assert res_aruns.json()["items"][0]["valid_apdi_count"] == 1


# =============================================================================
# 11. CORS Preflight Tests
# =============================================================================
def test_cors_options_preflight(empty_client: TestClient):
    # Allowed origin
    res = empty_client.options(
        "/api/v1/matches",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "http://localhost:3000"
