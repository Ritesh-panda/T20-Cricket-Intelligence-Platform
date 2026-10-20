"""Test Suite for Phase 3 Acquisition Pipeline.

Tests URL normalization, discovery deduplication, state machine transitions,
polite fetcher retry/backoff, 429 and 5xx handling, conditional requests,
content-type checks, redirect validation, idempotent duplicate ingestion,
legitimate source updates, transaction rollback, and entity linking.
"""
from __future__ import annotations

import io
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict
from unittest.mock import MagicMock, patch
import pytest
import requests

from src.models.canonical import ArticleParagraphRecord, ArticleRecord, SourceRecord
from src.pipeline.config import RetentionPolicy, SourceCategory, SourceConfig, SourceRegistry
from src.pipeline.discovery import DiscoveryEngine
from src.pipeline.entity_linker import EntityLinker, MatchLinkCandidate
from src.pipeline.fetcher import (
    ContentTypeMismatchError,
    DisallowedRedirectError,
    FetchError,
    FetchResult,
    ResponsibleFetcher,
    ResponseTooLargeError,
    RobotsDisallowedError,
)
from src.pipeline.orchestrator import AcquisitionOrchestrator
from src.pipeline.state_machine import (
    DiscoveredUrlRecord,
    IllegalStateTransitionError,
    ResourceState,
    validate_transition,
)
from src.pipeline.url_normalizer import InvalidUrlError, generate_url_id, normalize_url
from src.storage.sqlite_manager import SQLiteStorageManager

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def temp_db(tmp_path: Path) -> SQLiteStorageManager:
    db_file = tmp_path / "test_pipeline.db"
    return SQLiteStorageManager(db_file)


@pytest.fixture
def sample_news_source() -> SourceConfig:
    return SourceConfig(
        source_id="espncricinfo",
        name="ESPNcricinfo",
        category=SourceCategory.NEWS,
        base_url="https://www.espncricinfo.com",
        discovery_endpoints=["https://www.espncricinfo.com/rss/feed.xml"],
        adapter_id="news",
        enabled=True,
        rate_limit_rps=0.0,  # Fast in tests
        request_timeout_sec=5,
        max_retries=2,
        max_response_bytes=1024 * 1024,
        supported_content_types=["text/html", "application/xhtml+xml", "application/rss+xml"],
        retention_policy=RetentionPolicy(store_full_text=False, store_summary_only=True),
        license_tag="FairUse-ResearchExtraction",
        allowed_domains=["www.espncricinfo.com", "espncricinfo.com"],
    )


# -----------------------------------------------------------------------------
# 1. URL Normalization Tests
# -----------------------------------------------------------------------------
def test_url_normalization_tracking_params_and_fragments():
    raw = "https://www.espncricinfo.com/story/ind-vs-sa-final-1411166?utm_source=twitter&ref=share&match_id=1411166#comments"
    norm = normalize_url(raw, allowed_domains=["espncricinfo.com"])
    # utm_source and ref stripped; match_id preserved; #comments fragment stripped
    assert norm == "https://www.espncricinfo.com/story/ind-vs-sa-final-1411166?match_id=1411166"


def test_url_normalization_domain_filtering():
    raw = "https://malicious-external-site.com/cricket-news"
    with pytest.raises(InvalidUrlError, match="not in permitted domains"):
        normalize_url(raw, allowed_domains=["espncricinfo.com", "cricbuzz.com"])


def test_url_normalization_invalid_scheme():
    with pytest.raises(InvalidUrlError, match="Unsupported scheme"):
        normalize_url("javascript:alert(1)")


# -----------------------------------------------------------------------------
# 2. Discovery Tests
# -----------------------------------------------------------------------------
def test_discovery_from_rss_feed(sample_news_source: SourceConfig):
    engine = DiscoveryEngine()
    rss_path = FIXTURES_DIR / "sample_rss.xml"
    with open(rss_path, "rb") as f:
        rss_bytes = f.read()

    discovered = engine.discover_from_source(
        sample_news_source,
        custom_payloads={sample_news_source.discovery_endpoints[0]: rss_bytes},
    )
    assert len(discovered) == 2
    # Verify tracking parameters were stripped
    assert "utm_source" not in discovered[0].canonical_url
    assert discovered[0].source_id == "espncricinfo"
    assert discovered[0].state == ResourceState.DISCOVERED


def test_discovery_from_sitemap():
    sitemap_source = SourceConfig(
        source_id="wisden",
        name="Wisden",
        category=SourceCategory.NEWS,
        base_url="https://wisden.com",
        discovery_endpoints=["https://wisden.com/sitemap.xml"],
        adapter_id="news",
        enabled=True,
        allowed_domains=["wisden.com"],
    )
    engine = DiscoveryEngine()
    sitemap_path = FIXTURES_DIR / "sample_sitemap.xml"
    with open(sitemap_path, "rb") as f:
        sitemap_bytes = f.read()

    discovered = engine.discover_from_source(
        sitemap_source,
        custom_payloads={sitemap_source.discovery_endpoints[0]: sitemap_bytes},
    )
    assert len(discovered) == 2
    assert "ind-vs-eng-semi-final-tactical-review" in discovered[0].canonical_url


def test_discovery_deduplication(sample_news_source: SourceConfig):
    engine = DiscoveryEngine()
    rss_path = FIXTURES_DIR / "sample_rss.xml"
    with open(rss_path, "rb") as f:
        rss_bytes = f.read()

    # Pass the same endpoint twice
    source_multi = sample_news_source.model_copy(
        update={"discovery_endpoints": [sample_news_source.discovery_endpoints[0], sample_news_source.discovery_endpoints[0]]}
    )
    discovered = engine.discover_from_source(
        source_multi,
        custom_payloads={sample_news_source.discovery_endpoints[0]: rss_bytes},
    )
    # Must deduplicate identical canonical URLs
    assert len(discovered) == 2


# -----------------------------------------------------------------------------
# 3. State Machine Tests
# -----------------------------------------------------------------------------
def test_state_machine_legal_and_illegal_transitions():
    # Legal transitions
    validate_transition(ResourceState.DISCOVERED, ResourceState.QUEUED)
    validate_transition(ResourceState.QUEUED, ResourceState.FETCHED)
    validate_transition(ResourceState.FETCHED, ResourceState.PARSED)
    validate_transition(ResourceState.PARSED, ResourceState.VALIDATED)
    validate_transition(ResourceState.VALIDATED, ResourceState.INGESTED)
    validate_transition(ResourceState.FETCHED, ResourceState.SKIPPED)

    # Illegal transition: DISCOVERED -> INGESTED (skipping validation)
    with pytest.raises(IllegalStateTransitionError, match="Illegal state transition"):
        validate_transition(ResourceState.DISCOVERED, ResourceState.INGESTED)


def test_state_machine_persistence(temp_db: SQLiteStorageManager):
    url_rec = DiscoveredUrlRecord(
        url_id="url_test_123",
        source_id="espncricinfo",
        raw_url="https://www.espncricinfo.com/test",
        canonical_url="https://www.espncricinfo.com/test",
        state=ResourceState.DISCOVERED,
    )
    new_cnt, _ = temp_db.record_discovered_urls([url_rec])
    assert new_cnt == 1

    temp_db.transition_url_state(url_rec.url_id, ResourceState.QUEUED)
    stored = temp_db.get_url_by_canonical("https://www.espncricinfo.com/test")
    assert stored is not None
    assert stored.state == ResourceState.QUEUED

    # Transition to FETCHED with attempt increment
    temp_db.transition_url_state(url_rec.url_id, ResourceState.FETCHED, http_status=200, increment_attempt=True)
    stored = temp_db.get_url_by_canonical("https://www.espncricinfo.com/test")
    assert stored.state == ResourceState.FETCHED
    assert stored.attempt_count == 1
    assert stored.http_status == 200


# -----------------------------------------------------------------------------
# 4. Fetcher Tests (Mocked)
# -----------------------------------------------------------------------------
def test_fetcher_retry_on_5xx(sample_news_source: SourceConfig):
    mock_session = MagicMock()
    # First response: 503, second: 200
    resp_503 = MagicMock()
    resp_503.status_code = 503
    resp_503.url = "https://www.espncricinfo.com/test"
    resp_503.history = []

    resp_200 = MagicMock()
    resp_200.status_code = 200
    resp_200.url = "https://www.espncricinfo.com/test"
    resp_200.headers = {"Content-Type": "text/html; charset=utf-8"}
    resp_200.history = []
    resp_200.iter_content.return_value = [b"<html>Mock Body</html>"]

    mock_session.get.side_effect = [resp_503, resp_200]

    fetcher = ResponsibleFetcher(session=mock_session)
    fetcher.check_robots_allowed = MagicMock(return_value=True)

    with patch("time.sleep", return_value=None):
        result = fetcher.fetch("https://www.espncricinfo.com/test", sample_news_source)

    assert result.status_code == 200
    assert result.content == b"<html>Mock Body</html>"
    assert mock_session.get.call_count == 2


def test_fetcher_429_retry_after(sample_news_source: SourceConfig):
    mock_session = MagicMock()
    resp_429 = MagicMock()
    resp_429.status_code = 429
    resp_429.headers = {"Retry-After": "1"}
    resp_429.url = "https://www.espncricinfo.com/test"
    resp_429.history = []

    resp_200 = MagicMock()
    resp_200.status_code = 200
    resp_200.url = "https://www.espncricinfo.com/test"
    resp_200.headers = {"Content-Type": "text/html"}
    resp_200.history = []
    resp_200.iter_content.return_value = [b"Success"]

    mock_session.get.side_effect = [resp_429, resp_200]

    fetcher = ResponsibleFetcher(session=mock_session)
    fetcher.check_robots_allowed = MagicMock(return_value=True)

    with patch("time.sleep", return_value=None) as mock_sleep:
        result = fetcher.fetch("https://www.espncricinfo.com/test", sample_news_source)
        assert mock_sleep.called

    assert result.status_code == 200


def test_fetcher_content_type_mismatch(sample_news_source: SourceConfig):
    mock_session = MagicMock()
    resp = MagicMock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/pdf"}
    resp.url = "https://www.espncricinfo.com/test.pdf"
    resp.history = []

    mock_session.get.return_value = resp

    fetcher = ResponsibleFetcher(session=mock_session)
    fetcher.check_robots_allowed = MagicMock(return_value=True)

    with pytest.raises(ContentTypeMismatchError, match="Unsupported Content-Type"):
        fetcher.fetch("https://www.espncricinfo.com/test.pdf", sample_news_source)


def test_fetcher_response_too_large(sample_news_source: SourceConfig):
    mock_session = MagicMock()
    resp = MagicMock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "text/html"}
    resp.url = "https://www.espncricinfo.com/large"
    resp.history = []
    # Feed chunks exceeding max_response_bytes (1MB in fixture)
    resp.iter_content.return_value = [b"X" * (512 * 1024), b"Y" * (600 * 1024)]

    mock_session.get.return_value = resp

    fetcher = ResponsibleFetcher(session=mock_session)
    fetcher.check_robots_allowed = MagicMock(return_value=True)

    with pytest.raises(ResponseTooLargeError, match="exceeded limit"):
        fetcher.fetch("https://www.espncricinfo.com/large", sample_news_source)


def test_fetcher_disallowed_redirect(sample_news_source: SourceConfig):
    mock_session = MagicMock()
    resp = MagicMock()
    resp.status_code = 200
    resp.url = "https://unauthorized-redirect.com/login"
    resp.history = [MagicMock(url="https://www.espncricinfo.com/test")]

    mock_session.get.return_value = resp

    fetcher = ResponsibleFetcher(session=mock_session)
    fetcher.check_robots_allowed = MagicMock(return_value=True)

    with pytest.raises(DisallowedRedirectError, match="outside permitted domains"):
        fetcher.fetch("https://www.espncricinfo.com/test", sample_news_source)


def test_fetcher_conditional_304(sample_news_source: SourceConfig):
    mock_session = MagicMock()
    resp = MagicMock()
    resp.status_code = 304
    resp.headers = {"ETag": 'W/"12345"'}
    resp.url = "https://www.espncricinfo.com/test"
    resp.history = []

    mock_session.get.return_value = resp

    fetcher = ResponsibleFetcher(session=mock_session)
    fetcher.check_robots_allowed = MagicMock(return_value=True)

    res = fetcher.fetch("https://www.espncricinfo.com/test", sample_news_source, etag='W/"12345"')
    assert res.is_not_modified is True
    assert res.status_code == 304


# -----------------------------------------------------------------------------
# 5. Idempotent Ingestion and Source Updates Tests
# -----------------------------------------------------------------------------
def test_idempotent_duplicate_article_ingestion(temp_db: SQLiteStorageManager):
    article1 = ArticleRecord(
        article_id="art_1",
        canonical_url="https://www.espncricinfo.com/story/match-report",
        headline="India Win Final",
        source_domain="espncricinfo.com",
        full_text="India defeated South Africa in a thrilling final in Barbados by seven runs.",
        summary="India won by seven runs.",
        raw_content_hash="aaaa1111" + "0" * 56,
    )
    paragraphs = [
        ArticleParagraphRecord(
            paragraph_id="art_1_p0",
            article_id="art_1",
            paragraph_index=0,
            text=article1.full_text,
            char_count=len(article1.full_text),
        )
    ]

    # First ingestion
    applied, msg, art_id = temp_db.upsert_article_with_paragraphs(article1, paragraphs)
    assert applied is True
    assert temp_db.get_article_count() == 1

    # Second ingestion with identical content hash -> SKIPPED
    applied2, msg2, art_id2 = temp_db.upsert_article_with_paragraphs(article1, paragraphs)
    assert applied2 is False
    assert "Duplicate" in msg2
    assert temp_db.get_article_count() == 1


def test_legitimate_source_article_update(temp_db: SQLiteStorageManager):
    url = "https://www.espncricinfo.com/story/live-report"
    article_v1 = ArticleRecord(
        article_id=ArticleRecord.generate_id(url),
        canonical_url=url,
        headline="Match Ongoing",
        source_domain="espncricinfo.com",
        full_text="India are 150/4 after 17 overs against South Africa in the final.",
        summary="India 150/4 in over 17.",
        raw_content_hash="bbbb1111" + "0" * 56,
    )
    p_v1 = [
        ArticleParagraphRecord(
            paragraph_id=f"{article_v1.article_id}_p0",
            article_id=article_v1.article_id,
            paragraph_index=0,
            text=article_v1.full_text,
            char_count=len(article_v1.full_text),
        )
    ]
    applied1, _, _ = temp_db.upsert_article_with_paragraphs(article_v1, p_v1)
    assert applied1 is True

    # Updated article: new text and new content hash
    article_v2 = ArticleRecord(
        article_id=ArticleRecord.generate_id(url),
        canonical_url=url,
        headline="India Win Championship",
        source_domain="espncricinfo.com",
        full_text="India defeated South Africa by seven runs to lift the T20 World Cup trophy.",
        summary="India won the final.",
        raw_content_hash="cccc2222" + "0" * 56,
    )
    p_v2 = [
        ArticleParagraphRecord(
            paragraph_id=f"{article_v2.article_id}_p0",
            article_id=article_v2.article_id,
            paragraph_index=0,
            text=article_v2.full_text,
            char_count=len(article_v2.full_text),
        )
    ]

    applied2, msg2, art_id2 = temp_db.upsert_article_with_paragraphs(article_v2, p_v2, allow_update=True)
    assert applied2 is True
    assert "Updated" in msg2
    # Still exactly 1 article
    assert temp_db.get_article_count() == 1

    # Verify article_revisions captured the update
    with temp_db._get_connection() as conn:
        revs = conn.execute("SELECT * FROM article_revisions WHERE article_id = ?", (article_v1.article_id,)).fetchall()
        assert len(revs) == 1
        assert revs[0]["old_content_hash"] == article_v1.raw_content_hash
        assert revs[0]["new_content_hash"] == article_v2.raw_content_hash

        # Verify updated headline
        art_row = conn.execute("SELECT headline FROM articles WHERE article_id = ?", (article_v1.article_id,)).fetchone()
        assert art_row["headline"] == "India Win Championship"


# -----------------------------------------------------------------------------
# 6. Pipeline Orchestration & Resumption Tests
# -----------------------------------------------------------------------------
def test_interrupted_run_and_resumption(temp_db: SQLiteStorageManager, tmp_path: Path):
    cfg_file = tmp_path / "sources.yaml"
    cfg_file.write_text(
        """
sources:
  espncricinfo:
    source_id: "espncricinfo"
    name: "ESPNcricinfo"
    category: "news"
    base_url: "https://www.espncricinfo.com"
    discovery_endpoints: ["https://www.espncricinfo.com/rss.xml"]
    adapter_id: "news"
    enabled: true
    rate_limit_rps: 0.0
    allowed_domains: ["www.espncricinfo.com"]
"""
    )
    registry = SourceRegistry(cfg_file)

    # Insert a failed URL
    failed_url = DiscoveredUrlRecord(
        url_id="url_failed_1",
        source_id="espncricinfo",
        raw_url="https://www.espncricinfo.com/story/failed-item",
        canonical_url="https://www.espncricinfo.com/story/failed-item",
        state=ResourceState.FAILED,
        attempt_count=2,
        error_message="Simulated connection timeout",
    )
    temp_db.record_discovered_urls([failed_url])

    # Check reset_retryable_urls
    reset_cnt = temp_db.reset_retryable_urls(source_id="espncricinfo")
    assert reset_cnt == 1

    resumed = temp_db.get_url_by_canonical(failed_url.canonical_url)
    assert resumed.state == ResourceState.QUEUED


def test_database_transaction_rollback_on_failure(temp_db: SQLiteStorageManager):
    """Verifies that an error halfway through a multi-step storage write rolls back."""
    from src.models.canonical import TeamRecord

    team = TeamRecord(team_id="IND", name="India")
    temp_db.upsert_team(team)

    # Attempt an insertion that will raise an exception inside a transaction
    try:
        with temp_db._get_connection() as conn:
            conn.execute("INSERT INTO teams (team_id, name, aliases_json) VALUES ('ENG', 'England', '[]')")
            # Force integrity error (duplicate primary key without ON CONFLICT)
            conn.execute("INSERT INTO teams (team_id, name, aliases_json) VALUES ('IND', 'Duplicate India', '[]')")
    except Exception:
        pass

    # ENG should have been rolled back because the transaction failed!
    with temp_db._get_connection() as conn:
        eng = conn.execute("SELECT * FROM teams WHERE team_id = 'ENG'").fetchone()
        assert eng is None


def test_partial_source_failure_isolation(temp_db: SQLiteStorageManager, tmp_path: Path):
    """Verifies that one failing source does not halt execution for other sources."""
    cfg_file = tmp_path / "sources.yaml"
    cfg_file.write_text(
        """
sources:
  source_ok:
    source_id: "source_ok"
    name: "Source OK"
    category: "news"
    base_url: "https://www.espncricinfo.com"
    discovery_endpoints: ["https://www.espncricinfo.com/ok.xml"]
    adapter_id: "news"
    enabled: true
    rate_limit_rps: 0.0
    allowed_domains: ["www.espncricinfo.com"]

  source_bad:
    source_id: "source_bad"
    name: "Source Bad"
    category: "news"
    base_url: "https://bad-domain.invalid"
    discovery_endpoints: ["https://bad-domain.invalid/fail.xml"]
    adapter_id: "news"
    enabled: true
    rate_limit_rps: 0.0
    allowed_domains: ["bad-domain.invalid"]
"""
    )
    registry = SourceRegistry(cfg_file)
    sample_article_html = (FIXTURES_DIR / "sample_article.html").read_bytes()

    orchestrator = AcquisitionOrchestrator(registry=registry, storage=temp_db)

    # Mock bad source failure
    orchestrator.fetcher.fetch = MagicMock(side_effect=FetchError("Connection refused to bad host"))

    # Run bad source -> should record failure but not crash
    metrics_bad = orchestrator.run_source("source_bad")
    assert metrics_bad.source_id == "source_bad"

    # Now mock OK source success
    orchestrator.discovery_engine.discover_from_source = MagicMock(
        return_value=[
            DiscoveredUrlRecord(
                url_id="url_ok_1",
                source_id="source_ok",
                raw_url="https://www.espncricinfo.com/sample",
                canonical_url="https://www.espncricinfo.com/sample",
                state=ResourceState.DISCOVERED,
            )
        ]
    )
    metrics_ok = orchestrator.run_source(
        "source_ok",
        mock_payloads={"https://www.espncricinfo.com/sample": sample_article_html},
    )
    assert metrics_ok.records_ingested == 1


# -----------------------------------------------------------------------------
# 7. Entity Linking Tests
# -----------------------------------------------------------------------------
def test_entity_linker_conservative_matching(temp_db: SQLiteStorageManager):
    from src.models.canonical import MatchRecord, TeamRecord

    # Seed ground-truth teams and match
    temp_db.upsert_team(TeamRecord(team_id="IND", name="India", aliases=["Team India", "Men in Blue"]))
    temp_db.upsert_team(TeamRecord(team_id="SA", name="South Africa", aliases=["Proteas"]))

    match = MatchRecord(
        match_id="match_t20wc_final_2024",
        tournament="ICC Men's T20 World Cup",
        season="2024",
        match_date="2024-06-29",
        venue="Kensington Oval, Bridgetown",
        city="Barbados",
        team1_id="IND",
        team2_id="SA",
        winner_id="IND",
    )
    temp_db.upsert_match(match)

    linker = EntityLinker(temp_db)

    # High-confidence article: both teams + tournament + exact date
    headline = "India beat South Africa in breathtaking T20 World Cup final"
    body = "Virat Kohli made 76 as India held off a late surge by South Africa in Barbados."
    pub_date = datetime(2024, 6, 29, 20, 0, tzinfo=timezone.utc)

    candidate = linker.resolve_match_link(headline, body, pub_date)
    assert candidate is not None
    assert candidate.match_id == "match_t20wc_final_2024"
    assert candidate.confidence >= 0.70
    assert "IND" in candidate.evidence["teams_matched"]
    assert "SA" in candidate.evidence["teams_matched"]

    # Low-confidence / generic article -> should return None (not forced!)
    generic_headline = "Top 5 fielding moments of the season"
    generic_body = "Cricket has seen remarkable athletic catches across various franchise leagues."
    candidate2 = linker.resolve_match_link(generic_headline, generic_body, pub_date)
    assert candidate2 is None
