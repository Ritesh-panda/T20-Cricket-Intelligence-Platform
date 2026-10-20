"""Unit tests for SQLite and Parquet storage managers."""
import pytest
from datetime import datetime, timezone
from pathlib import Path

from src.models.canonical import (
    ArticleParagraphRecord,
    ArticleRecord,
    DeliveryRecord,
    MatchPhase,
    MatchRecord,
    PlayerRecord,
    SourceRecord,
    TeamRecord,
)
from src.storage.parquet_manager import ParquetStorageManager
from src.storage.sqlite_manager import SQLiteStorageManager


@pytest.fixture
def temp_storage(tmp_path):
    db_path = tmp_path / "test_cricket.db"
    parquet_dir = tmp_path / "parquet"
    sql_mgr = SQLiteStorageManager(db_path)
    parq_mgr = ParquetStorageManager(parquet_dir)
    return sql_mgr, parq_mgr


def test_sqlite_provenance_deduplication(temp_storage):
    sql_mgr, _ = temp_storage
    rec1 = SourceRecord(
        provenance_id="prov_001",
        source_name="cricsheet",
        source_identifier="match1.json",
        harvest_timestamp_utc=datetime.now(timezone.utc),
        content_hash_sha256="1" * 64,
        license_tag="ODbL-1.0",
        redistributable=True,
    )
    # First insert succeeds
    assert sql_mgr.record_provenance(rec1) is True
    # Duplicate insert on same content hash returns False
    rec2 = SourceRecord(
        provenance_id="prov_002",
        source_name="cricsheet",
        source_identifier="match1_copy.json",
        harvest_timestamp_utc=datetime.now(timezone.utc),
        content_hash_sha256="1" * 64,  # Identical hash!
        license_tag="ODbL-1.0",
        redistributable=True,
    )
    assert sql_mgr.record_provenance(rec2) is False


def test_sqlite_match_and_delivery_roundtrip(temp_storage):
    sql_mgr, _ = temp_storage
    team1 = TeamRecord(team_id="IND", name="India", aliases=["IND"])
    team2 = TeamRecord(team_id="SA", name="South Africa", aliases=["SA"])
    sql_mgr.upsert_team(team1)
    sql_mgr.upsert_team(team2)

    match = MatchRecord(
        match_id="match_test_01",
        tournament="ICC Men's T20 World Cup",
        season="2024",
        match_date="2024-06-29",
        venue="Kensington Oval",
        team1_id="IND",
        team2_id="SA",
        winner_id="IND",
        win_by_runs=7,
        target_runs=177,
    )
    sql_mgr.upsert_match(match)
    assert sql_mgr.get_match_count() == 1

    deliv1 = DeliveryRecord(
        delivery_id="del_match_test_01_inn1_ov0_b1",
        match_id="match_test_01",
        innings=1,
        over=0,
        ball=1,
        batter_id="player_rohit",
        bowler_id="player_jansen",
        batter_runs=4,
        extra_runs=0,
        total_runs=4,
        is_legal=True,
        is_wicket=False,
        phase=MatchPhase.POWERPLAY,
    )
    inserted = sql_mgr.insert_deliveries_batch([deliv1])
    assert inserted == 1
    assert sql_mgr.get_delivery_count() == 1

    # Idempotent re-insert does not duplicate
    reinserted = sql_mgr.insert_deliveries_batch([deliv1])
    assert reinserted == 0
    assert sql_mgr.get_delivery_count() == 1


def test_sqlite_article_deduplication(temp_storage):
    sql_mgr, _ = temp_storage
    url = "https://www.espncricinfo.com/sample-article"
    art_id = ArticleRecord.generate_id(url)
    content = "India defeated South Africa in a nail-biting encounter at Barbados."
    h = "c" * 64

    art = ArticleRecord(
        article_id=art_id,
        canonical_url=url,
        headline="Barbados Thriller",
        author="Reporter",
        published_at_utc=datetime.now(timezone.utc),
        source_domain="espncricinfo.com",
        full_text=content,
        language="en",
        raw_content_hash=h,
    )
    p = ArticleParagraphRecord(
        paragraph_id=f"{art_id}_p0",
        article_id=art_id,
        paragraph_index=0,
        text=content,
        char_count=len(content),
    )

    inserted, _ = sql_mgr.insert_article_with_paragraphs(art, [p])
    assert inserted is True
    assert sql_mgr.get_article_count() == 1

    # Attempt inserting duplicate
    dup_inserted, reason = sql_mgr.insert_article_with_paragraphs(art, [p])
    assert dup_inserted is False
    assert "Duplicate detected" in reason
    assert sql_mgr.get_article_count() == 1


def test_parquet_storage_roundtrip(temp_storage):
    _, parq_mgr = temp_storage
    deliv = DeliveryRecord(
        delivery_id="del_parq_01",
        match_id="match_parq",
        innings=1,
        over=0,
        ball=1,
        batter_id="player_batter",
        bowler_id="player_bowler",
        batter_runs=1,
        extra_runs=0,
        total_runs=1,
        is_legal=True,
        is_wicket=False,
        phase=MatchPhase.POWERPLAY,
    )
    target = parq_mgr.write_deliveries([deliv])
    assert target.exists()

    df = parq_mgr.read_deliveries(match_id="match_parq")
    assert len(df) == 1
    assert df.iloc[0]["delivery_id"] == "del_parq_01"
    assert df.iloc[0]["total_runs"] == 1
