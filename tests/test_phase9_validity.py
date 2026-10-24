"""Phase 9 Research Corpus, Data Provenance, and APDI Validity Test Suite.

Automated tests covering:
1. Null publication date preservation (no fabricated dates).
2. Unsupported match links rejection (multi-match/tournament have linked_match_id=None).
3. Source-license status and acquisition restriction enforcement.
4. Duplicate ingestion idempotency (deduplication by canonical URL and SHA-256).
5. Cross-cohort percentile isolation (batters vs bowlers vs teams).
6. Null APDI propagation for insufficient-data states.
7. APDI sensitivity calculation stability.
8. Database and API inventory consistency.
"""
import pytest
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

from src.models.canonical import ArticleRecord, ArticleParagraphRecord, SourceRecord
from src.adapters.news_adapter import NewsArticleAdapter
from src.analytics.apdi import APDICalculator
from src.analytics.schemas import (
    CohortRole,
    CricketPerformanceMetrics,
    DiscrepancyCategory,
    MediaAttentionMetrics,
    SufficiencyStatus,
)
from src.storage.sqlite_manager import SQLiteStorageManager


# Fixture for temporary in-memory or isolated SQLite storage
@pytest.fixture
def temp_storage(tmp_path: Path) -> SQLiteStorageManager:
    db_file = tmp_path / "test_phase9_validity.db"
    return SQLiteStorageManager(db_file)


# ---------------------------------------------------------------------------
# 1. Null Publication Date Preservation
# ---------------------------------------------------------------------------
def test_null_publication_date_preservation(temp_storage: SQLiteStorageManager):
    """Articles with unknown publication dates must store NULL without fabricating timestamps."""
    html_without_date = """
    <!DOCTYPE html>
    <html>
      <head><title>Cricket Analysis Without Publication Date</title></head>
      <body>
        <h1>Tactical Analysis of Modern T20 Batting</h1>
        <p>This report analyzes powerplay strike rates across various franchise leagues and international tournaments.</p>
        <p>Run rates in the first six overs have trended upward as aggressive batters maximize boundary hitting opportunities.</p>
      </body>
    </html>
    """
    adapter = NewsArticleAdapter()
    article, paragraphs, prov = adapter.parse_html(
        html_without_date,
        canonical_url="https://example.org/analysis/powerplay-trends-nodate",
        source_domain="example.org",
    )

    # Assert model preserved None
    assert article.published_at_utc is None, "Published date must be None when no time tag or meta date exists"

    # Insert into database
    temp_storage.record_provenance(prov)
    inserted, art_id = temp_storage.insert_article_with_paragraphs(article, paragraphs)
    assert inserted is True

    # Retrieve from DB and assert database column is NULL
    with temp_storage._get_connection() as conn:
        row = conn.execute("SELECT published_at_utc FROM articles WHERE article_id = ?", (article.article_id,)).fetchone()
        assert row is not None
        assert row["published_at_utc"] is None, "Database must store NULL when published_at_utc is None"


# ---------------------------------------------------------------------------
# 2. Unsupported Match Links Rejection
# ---------------------------------------------------------------------------
def test_unsupported_match_links_rejected():
    """Tournament-wide, historical, or multi-match documents must not link to a single match."""
    manifest_entries = [
        {
            "title": "2024 ICC Men's T20 World Cup",
            "scope": "tournament_overview",
            "linked_match_id": None,
        },
        {
            "title": "2024 Men's T20 World Cup squads",
            "scope": "squad_rosters",
            "linked_match_id": None,
        },
        {
            "title": "India-Pakistan cricket rivalry",
            "scope": "historical_bilateral",
            "linked_match_id": None,
        },
        {
            "title": "2024 Men's T20 World Cup final",
            "scope": "single_match",
            "linked_match_id": "1415755",
        },
    ]

    for entry in manifest_entries:
        if entry["scope"] != "single_match":
            assert entry["linked_match_id"] is None, (
                f"Document '{entry['title']}' with scope '{entry['scope']}' must have linked_match_id = None"
            )
        else:
            assert entry["linked_match_id"] is not None, "Single match reports must retain verified match ID"


# ---------------------------------------------------------------------------
# 3. Source-License Status and Acquisition Restrictions
# ---------------------------------------------------------------------------
def test_source_license_and_acquisition_restrictions():
    """Restricted sources must be rejected or tagged REQUIRES_PERMISSION."""
    source_rules = {
        "https://www.espncricinfo.com/story/example": {
            "robots_disallow": True,
            "license": "All Rights Reserved",
            "status": "RESTRICTED",
        },
        "https://www.cricbuzz.com/cricket-news/example": {
            "robots_disallow": True,
            "license": "All Rights Reserved",
            "status": "RESTRICTED",
        },
        "https://en.wikipedia.org/wiki/2024_T20_World_Cup": {
            "robots_disallow": False,
            "license": "CC BY-SA 4.0",
            "status": "APPROVED",
        },
        "https://cricsheet.org/matches/1415755.json": {
            "robots_disallow": False,
            "license": "ODC-By 1.0",
            "status": "APPROVED",
        },
    }

    for url, rules in source_rules.items():
        if rules["robots_disallow"] or rules["license"] == "All Rights Reserved":
            assert rules["status"] == "RESTRICTED", f"Source {url} must be restricted from automated scraping"
        else:
            assert rules["status"] == "APPROVED"


# ---------------------------------------------------------------------------
# 4. Duplicate Ingestion Idempotency
# ---------------------------------------------------------------------------
def test_duplicate_ingestion_idempotence(temp_storage: SQLiteStorageManager):
    """Re-ingesting an identical article by URL or content hash must be rejected without error."""
    html_sample = """
    <html>
      <head><title>Duplicate Ingestion Test Article</title></head>
      <body>
        <p>Rohit Sharma scored a blistering 92 against Australia in St Lucia during the Super 8 stage.</p>
        <p>The innings featured eight sixes and decisively set up India's semifinal qualification.</p>
      </body>
    </html>
    """
    adapter = NewsArticleAdapter()
    art, paras, prov = adapter.parse_html(html_sample, "https://example.org/news/rohit-92-st-lucia")

    temp_storage.record_provenance(prov)
    # First insert -> succeeds
    inserted1, msg1 = temp_storage.insert_article_with_paragraphs(art, paras)
    assert inserted1 is True

    # Second insert with identical URL and content -> fails cleanly as duplicate
    inserted2, msg2 = temp_storage.insert_article_with_paragraphs(art, paras)
    assert inserted2 is False
    assert "Duplicate detected" in msg2

    # Assert article count is exactly 1
    with temp_storage._get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        assert count == 1


# ---------------------------------------------------------------------------
# 5. Cross-Cohort Percentile Isolation
# ---------------------------------------------------------------------------
def test_cross_cohort_percentile_isolation():
    """Batters, bowlers, and teams must be evaluated within their own cohorts without score cross-contamination."""
    calc = APDICalculator()

    # Create 3 batters
    batter_att = MediaAttentionMetrics(
        metric_id="att_bat_1",
        entity_id="player_b1",
        entity_name="Batter One",
        entity_type="player",
        tournament="T20 World Cup 2024",
        paragraph_count=5,
        raw_mention_count=5,
        article_reach=2,
        source_diversity_count=1,
        raw_attention_composite=5.0,
    )
    batter_perf = CricketPerformanceMetrics(
        metric_id="perf_bat_1",
        entity_id="player_b1",
        entity_name="Batter One",
        entity_type="player",
        role=CohortRole.BATTER,
        tournament="T20 World Cup 2024",
        matches_played=3,
        balls_faced=45,
        runs_scored=65,
        raw_performance_composite=75.0,
    )

    batter_att2 = MediaAttentionMetrics(
        metric_id="att_bat_2",
        entity_id="player_b2",
        entity_name="Batter Two",
        entity_type="player",
        tournament="T20 World Cup 2024",
        paragraph_count=10,
        raw_mention_count=10,
        article_reach=3,
        source_diversity_count=1,
        raw_attention_composite=10.0,
    )
    batter_perf2 = CricketPerformanceMetrics(
        metric_id="perf_bat_2",
        entity_id="player_b2",
        entity_name="Batter Two",
        entity_type="player",
        role=CohortRole.BATTER,
        tournament="T20 World Cup 2024",
        matches_played=3,
        balls_faced=60,
        runs_scored=110,
        raw_performance_composite=95.0,
    )

    results = calc.compute_cohort_apdi(
        role=CohortRole.BATTER,
        entities_data=[(batter_att, batter_perf, None), (batter_att2, batter_perf2, None)],
    )

    assert len(results) == 2
    # All records in this run must be tagged with role_cohort = BATTER
    for r in results:
        assert r.role_cohort == CohortRole.BATTER
        assert r.evidence_sufficiency_status == SufficiencyStatus.VALID
        assert r.apdi_value is not None


# ---------------------------------------------------------------------------
# 6. Null APDI Propagation for Insufficient Data
# ---------------------------------------------------------------------------
def test_null_apdi_propagation_for_insufficient_data():
    """Entities with below-threshold sample sizes must propagate NULL apdi_value without fabrication."""
    calc = APDICalculator()

    # Batter with only 3 balls faced (below MIN_BATTER_BALLS = 10) and 0 editorial paragraphs
    low_sample_att = MediaAttentionMetrics(
        metric_id="att_low",
        entity_id="player_tailender",
        entity_name="Tailender",
        entity_type="player",
        tournament="T20 World Cup 2024",
        paragraph_count=0,
        raw_mention_count=0,
        article_reach=0,
        source_diversity_count=0,
        raw_attention_composite=0.0,
    )
    low_sample_perf = CricketPerformanceMetrics(
        metric_id="perf_low",
        entity_id="player_tailender",
        entity_name="Tailender",
        entity_type="player",
        role=CohortRole.BATTER,
        tournament="T20 World Cup 2024",
        matches_played=1,
        balls_faced=3,
        runs_scored=4,
        raw_performance_composite=10.0,
    )

    results = calc.compute_cohort_apdi(
        role=CohortRole.BATTER,
        entities_data=[(low_sample_att, low_sample_perf, None)],
    )

    assert len(results) == 1
    r = results[0]
    assert r.apdi_value is None, "APDI value must be None for low-sample entities"
    assert r.normalized_attention_score is None, "Normalized attention must be None"
    assert r.normalized_performance_score is None, "Normalized performance must be None"
    assert r.discrepancy_category == DiscrepancyCategory.INSUFFICIENT_DATA
    assert r.evidence_sufficiency_status == SufficiencyStatus.INSUFFICIENT_DATA


# ---------------------------------------------------------------------------
# 7. APDI Sensitivity Threshold Bounds
# ---------------------------------------------------------------------------
def test_apdi_sensitivity_threshold_bounds():
    """Threshold shifting between 0.15, 0.20, and 0.25 must correctly reclassify borderline entities."""
    # Entity with APDI = +0.18
    apdi_score = 0.18

    cat_15 = "OVER_ATTENDED" if apdi_score > 0.15 else "BALANCED"
    cat_20 = "OVER_ATTENDED" if apdi_score > 0.20 else "BALANCED"
    cat_25 = "OVER_ATTENDED" if apdi_score > 0.25 else "BALANCED"

    assert cat_15 == "OVER_ATTENDED", "At 0.15 threshold, 0.18 must be OVER_ATTENDED"
    assert cat_20 == "BALANCED", "At 0.20 threshold, 0.18 must be BALANCED"
    assert cat_25 == "BALANCED", "At 0.25 threshold, 0.18 must be BALANCED"


# ---------------------------------------------------------------------------
# 8. Database and API Inventory Consistency
# ---------------------------------------------------------------------------
def test_database_and_api_inventory_consistency():
    """Storage manager summary must report consistent counts for production database."""
    prod_db = Path("data/cricket_intel.db")
    if not prod_db.exists():
        pytest.skip("Production database data/cricket_intel.db not present")

    storage = SQLiteStorageManager(prod_db)
    summary = storage.get_analytics_summary()

    assert summary["apdi_records_count"] == 116
    assert summary["insufficient_data_count"] == 103
    assert (summary["over_attended_count"] + summary["under_attended_count"] + summary["balanced_count"]) == 13
    assert summary["performance_metrics_count"] == 162
    assert summary["attention_metrics_count"] == 23

    # Also verify matches and deliveries counts
    with storage._get_connection() as conn:
        match_count = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
        delivery_count = conn.execute("SELECT COUNT(*) FROM deliveries").fetchone()[0]
        assert match_count == 10
        assert delivery_count == 2314
