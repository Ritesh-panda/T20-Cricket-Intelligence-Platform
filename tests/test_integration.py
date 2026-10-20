"""End-to-End Integration Tests for Phase 2 Data Foundation."""
from pathlib import Path
import pytest

from src.adapters.cricsheet_adapter import CricsheetAdapter
from src.adapters.commentary_adapter import CommentaryAdapter
from src.adapters.news_adapter import NewsArticleAdapter
from src.models.canonical import EventAlignmentRecord
from src.storage.parquet_manager import ParquetStorageManager
from src.storage.sqlite_manager import SQLiteStorageManager


@pytest.fixture
def fixtures_dir():
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def storage_env(tmp_path):
    db_path = tmp_path / "integration_cricket.db"
    parquet_dir = tmp_path / "processed_parquet"
    return SQLiteStorageManager(db_path), ParquetStorageManager(parquet_dir)


def test_full_ingestion_and_provenance_pipeline(fixtures_dir, storage_env):
    sql_mgr, parq_mgr = storage_env

    # 1. Start Ingestion Run
    run = sql_mgr.start_ingestion_run(source_name="e2e_integration_test")

    # 2. Ingest Cricsheet match
    cric_adapter = CricsheetAdapter()
    cric_res = cric_adapter.parse_file(fixtures_dir / "cricsheet_sample_t20.json")

    # Store Cricsheet Provenance, Teams, Players, Matches, and Deliveries
    sql_mgr.record_provenance(cric_res.provenance)
    for team in cric_res.teams:
        sql_mgr.upsert_team(team)
    for player in cric_res.players:
        sql_mgr.upsert_player(player)
    sql_mgr.upsert_match(cric_res.match)
    deliv_inserted = sql_mgr.insert_deliveries_batch(cric_res.deliveries)

    # Parquet export
    parq_mgr.write_matches([cric_res.match])
    parq_mgr.write_deliveries(cric_res.deliveries)

    assert deliv_inserted > 0
    assert sql_mgr.get_match_count() == 1
    assert sql_mgr.get_delivery_count() == len(cric_res.deliveries)

    # 3. Ingest Commentary Feed
    comm_adapter = CommentaryAdapter()
    with open(fixtures_dir / "sample_commentary.txt", "r", encoding="utf-8") as f:
        comm_text = f.read()

    comm_records, unparsed = comm_adapter.parse_raw_text(
        raw_text=comm_text,
        match_id=cric_res.match.match_id,
        innings=1,
        source_domain="cricbuzz.com",
    )
    comm_inserted = sql_mgr.insert_commentary_batch(comm_records)
    assert comm_inserted == len(comm_records)
    assert sql_mgr.get_commentary_count() == len(comm_records)

    # 4. Ingest News Article
    news_adapter = NewsArticleAdapter()
    with open(fixtures_dir / "sample_article.html", "r", encoding="utf-8") as f:
        article_html = f.read()

    art_url = "https://www.wisden.com/matches/reports/t20-world-cup-final-2024"
    article, paragraphs, art_prov = news_adapter.parse_html(
        html_content=article_html,
        canonical_url=art_url,
        source_domain="wisden.com",
    )
    sql_mgr.record_provenance(art_prov)
    art_inserted, art_id = sql_mgr.insert_article_with_paragraphs(article, paragraphs)
    assert art_inserted is True
    assert sql_mgr.get_article_count() == 1

    # 5. Cross-Source Event Alignment (Paragraph 4 -> Match 19th Over)
    # Paragraph 4 describes Hardik Pandya defending 16 runs and Suryakumar catch
    death_paragraph = next(p for p in paragraphs if "Pandya defended 16 runs" in p.text)
    alignment = EventAlignmentRecord(
        alignment_id=f"align_{death_paragraph.paragraph_id}_{cric_res.match.match_id}_inn2_ov19",
        paragraph_id=death_paragraph.paragraph_id,
        match_id=cric_res.match.match_id,
        innings=2,
        over_window_start=19,
        over_window_end=19,
        confidence_score=0.96,
        alignment_method="hybrid_v1",
        supporting_evidence={
            "matching_entities": ["player_hardik_pandya", "player_david_miller", "player_suryakumar_yadav"],
            "temporal_proximity_hours": 2.5,
            "event_keywords": ["caught", "final over", "defended 16"],
        },
    )
    align_inserted = sql_mgr.insert_alignments([alignment])
    assert align_inserted == 1

    # 6. Verify Idempotence & Restartability (Repeat entire ingestion)
    repeat_deliv = sql_mgr.insert_deliveries_batch(cric_res.deliveries)
    assert repeat_deliv == 0  # 0 duplicates added!
    assert sql_mgr.get_delivery_count() == len(cric_res.deliveries)

    repeat_comm = sql_mgr.insert_commentary_batch(comm_records)
    assert repeat_comm == 0
    assert sql_mgr.get_commentary_count() == len(comm_records)

    repeat_art, _ = sql_mgr.insert_article_with_paragraphs(article, paragraphs)
    assert repeat_art is False  # Correctly rejected as duplicate!
    assert sql_mgr.get_article_count() == 1

    # Parquet read verification
    deliv_df = parq_mgr.read_deliveries(match_id=cric_res.match.match_id)
    assert len(deliv_df) == len(cric_res.deliveries)

    # 7. Complete Ingestion Run
    run.status = "completed"
    run.records_extracted = len(cric_res.deliveries) + len(comm_records) + len(paragraphs)
    run.records_ingested = run.records_extracted
    sql_mgr.update_ingestion_run(run)
