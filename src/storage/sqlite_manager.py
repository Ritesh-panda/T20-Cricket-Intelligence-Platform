"""SQLite Storage Manager for T20 Cricket Intelligence Platform.

Provides thread-safe, transactional persistence for metadata, provenance,
articles, commentary, and match entities with idempotent upserts and deduplication.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.models.canonical import (
    ArticleParagraphRecord,
    ArticleRecord,
    CommentaryRecord,
    DeliveryRecord,
    EventAlignmentRecord,
    IngestionRun,
    MatchRecord,
    PlayerRecord,
    SourceRecord,
    TeamRecord,
)
from src.pipeline.state_machine import (
    DiscoveredUrlRecord,
    ResourceState,
    validate_transition,
)
from src.nlp.schemas import (
    EntityMentionRecord,
    EntityResolutionRecord,
    NLPRunRecord,
    NormalizedTextRecord,
    SentimentBaselineRecord,
)
from src.analysis.analysis_schemas import (
    EmbeddingMetadataRecord,
    TopicRunRecord,
    TopicClusterRecord,
    TopicAssignmentRecord,
    CrossSourceMatchRecord,
    NarrativeTimelinePoint,
)

SCHEMA_VERSION = 4

DDL_SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ingestion_runs (
    run_id TEXT PRIMARY KEY,
    source_name TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at_utc TEXT NOT NULL,
    completed_at_utc TEXT,
    records_extracted INTEGER DEFAULT 0,
    records_ingested INTEGER DEFAULT 0,
    records_skipped INTEGER DEFAULT 0,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS source_records (
    provenance_id TEXT PRIMARY KEY,
    source_name TEXT NOT NULL,
    source_identifier TEXT NOT NULL,
    source_url TEXT,
    harvest_timestamp_utc TEXT NOT NULL,
    http_status INTEGER,
    content_hash_sha256 TEXT UNIQUE NOT NULL,
    pipeline_version TEXT NOT NULL,
    license_tag TEXT NOT NULL,
    redistributable INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS teams (
    team_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    aliases_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS players (
    player_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    cricsheet_id TEXT,
    primary_team_id TEXT,
    batting_style TEXT,
    bowling_style TEXT,
    aliases_json TEXT NOT NULL,
    FOREIGN KEY(primary_team_id) REFERENCES teams(team_id)
);

CREATE TABLE IF NOT EXISTS matches (
    match_id TEXT PRIMARY KEY,
    tournament TEXT NOT NULL,
    season TEXT NOT NULL,
    match_date TEXT NOT NULL,
    venue TEXT NOT NULL,
    city TEXT,
    team1_id TEXT NOT NULL,
    team2_id TEXT NOT NULL,
    toss_winner_id TEXT,
    toss_decision TEXT,
    winner_id TEXT,
    win_by_runs INTEGER,
    win_by_wickets INTEGER,
    player_of_match_id TEXT,
    target_runs INTEGER,
    metadata_json TEXT NOT NULL,
    provenance_id TEXT,
    FOREIGN KEY(team1_id) REFERENCES teams(team_id),
    FOREIGN KEY(team2_id) REFERENCES teams(team_id),
    FOREIGN KEY(provenance_id) REFERENCES source_records(provenance_id)
);

CREATE TABLE IF NOT EXISTS deliveries (
    delivery_id TEXT PRIMARY KEY,
    match_id TEXT NOT NULL,
    innings INTEGER NOT NULL,
    over_num INTEGER NOT NULL,
    ball_num INTEGER NOT NULL,
    batter_id TEXT NOT NULL,
    bowler_id TEXT NOT NULL,
    non_striker_id TEXT,
    batter_runs INTEGER NOT NULL,
    extra_runs INTEGER NOT NULL,
    extra_type TEXT,
    total_runs INTEGER NOT NULL,
    is_legal INTEGER NOT NULL,
    is_wicket INTEGER NOT NULL,
    wicket_kind TEXT,
    player_dismissed_id TEXT,
    phase TEXT NOT NULL,
    FOREIGN KEY(match_id) REFERENCES matches(match_id)
);

CREATE TABLE IF NOT EXISTS articles (
    article_id TEXT PRIMARY KEY,
    canonical_url TEXT UNIQUE NOT NULL,
    headline TEXT NOT NULL,
    author TEXT,
    published_at_utc TEXT,
    source_domain TEXT NOT NULL,
    full_text TEXT NOT NULL,
    summary TEXT,
    language TEXT NOT NULL,
    raw_content_hash TEXT UNIQUE NOT NULL,
    provenance_id TEXT,
    FOREIGN KEY(provenance_id) REFERENCES source_records(provenance_id)
);

CREATE TABLE IF NOT EXISTS article_paragraphs (
    paragraph_id TEXT PRIMARY KEY,
    article_id TEXT NOT NULL,
    paragraph_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    char_count INTEGER NOT NULL,
    FOREIGN KEY(article_id) REFERENCES articles(article_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS commentary_entries (
    commentary_id TEXT PRIMARY KEY,
    match_id TEXT NOT NULL,
    innings INTEGER NOT NULL,
    over_num INTEGER NOT NULL,
    ball_num INTEGER NOT NULL,
    bowler_raw TEXT NOT NULL,
    batter_raw TEXT NOT NULL,
    text TEXT NOT NULL,
    event_tags_json TEXT NOT NULL,
    source_domain TEXT NOT NULL,
    harvest_timestamp_utc TEXT NOT NULL,
    provenance_id TEXT,
    FOREIGN KEY(match_id) REFERENCES matches(match_id)
);

CREATE TABLE IF NOT EXISTS event_alignments (
    alignment_id TEXT PRIMARY KEY,
    paragraph_id TEXT NOT NULL,
    match_id TEXT NOT NULL,
    innings INTEGER NOT NULL,
    over_window_start INTEGER NOT NULL,
    over_window_end INTEGER NOT NULL,
    confidence_score REAL NOT NULL,
    alignment_method TEXT NOT NULL,
    supporting_evidence_json TEXT NOT NULL,
    FOREIGN KEY(paragraph_id) REFERENCES article_paragraphs(paragraph_id),
    FOREIGN KEY(match_id) REFERENCES matches(match_id)
);

CREATE INDEX IF NOT EXISTS idx_deliv_match ON deliveries(match_id, innings, over_num);
CREATE INDEX IF NOT EXISTS idx_comm_match ON commentary_entries(match_id, innings, over_num);
CREATE INDEX IF NOT EXISTS idx_align_match ON event_alignments(match_id);
CREATE INDEX IF NOT EXISTS idx_art_url ON articles(canonical_url);
CREATE INDEX IF NOT EXISTS idx_art_hash ON articles(raw_content_hash);

CREATE TABLE IF NOT EXISTS article_revisions (
    revision_id TEXT PRIMARY KEY,
    article_id TEXT NOT NULL,
    revised_at_utc TEXT NOT NULL,
    old_content_hash TEXT NOT NULL,
    new_content_hash TEXT NOT NULL,
    provenance_id TEXT,
    FOREIGN KEY(article_id) REFERENCES articles(article_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS discovered_urls (
    url_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    raw_url TEXT NOT NULL,
    canonical_url TEXT UNIQUE NOT NULL,
    state TEXT NOT NULL,
    discovered_at_utc TEXT NOT NULL,
    last_attempt_at_utc TEXT,
    completed_at_utc TEXT,
    attempt_count INTEGER DEFAULT 0,
    http_status INTEGER,
    etag TEXT,
    last_modified TEXT,
    content_hash TEXT,
    error_message TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_disc_state ON discovered_urls(state);
CREATE INDEX IF NOT EXISTS idx_disc_source ON discovered_urls(source_id);
CREATE INDEX IF NOT EXISTS idx_disc_canon ON discovered_urls(canonical_url);

CREATE TABLE IF NOT EXISTS normalized_texts (
    norm_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    original_text TEXT NOT NULL,
    normalized_text TEXT NOT NULL,
    char_count INTEGER NOT NULL,
    pipeline_version TEXT NOT NULL,
    processed_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_norm_src ON normalized_texts(source_type, source_id);

CREATE TABLE IF NOT EXISTS entity_mentions (
    mention_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    surface_text TEXT NOT NULL,
    start_char INTEGER NOT NULL,
    end_char INTEGER NOT NULL,
    detection_method TEXT NOT NULL,
    confidence REAL NOT NULL,
    resolved_id TEXT,
    resolution_status TEXT NOT NULL,
    evidence_json TEXT NOT NULL DEFAULT '{}',
    pipeline_version TEXT NOT NULL,
    created_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_men_src ON entity_mentions(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_men_res ON entity_mentions(resolved_id);

CREATE TABLE IF NOT EXISTS entity_resolutions (
    resolution_id TEXT PRIMARY KEY,
    mention_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    score REAL NOT NULL,
    is_winner INTEGER NOT NULL,
    evidence_json TEXT NOT NULL DEFAULT '{}',
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY(mention_id) REFERENCES entity_mentions(mention_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_res_men ON entity_resolutions(mention_id);

CREATE TABLE IF NOT EXISTS sentiment_baselines (
    sentiment_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    target_entity_id TEXT,
    general_sentiment TEXT NOT NULL,
    event_polarity TEXT NOT NULL,
    framing_score REAL NOT NULL,
    compound_score REAL NOT NULL,
    evidence_tokens_json TEXT NOT NULL DEFAULT '[]',
    rule_applied TEXT NOT NULL,
    confidence REAL NOT NULL,
    pipeline_version TEXT NOT NULL,
    created_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sent_src ON sentiment_baselines(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_sent_target ON sentiment_baselines(target_entity_id);

CREATE TABLE IF NOT EXISTS nlp_runs (
    run_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    started_at_utc TEXT NOT NULL,
    completed_at_utc TEXT,
    records_processed INTEGER DEFAULT 0,
    mentions_extracted INTEGER DEFAULT 0,
    sentiment_scored INTEGER DEFAULT 0,
    errors_json TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS embedding_records (
    embedding_id TEXT PRIMARY KEY,
    norm_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    model_version TEXT NOT NULL,
    dimension INTEGER NOT NULL,
    text_hash TEXT NOT NULL,
    is_test_double INTEGER NOT NULL DEFAULT 0,
    vector_file_path TEXT,
    vector_index INTEGER,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY(norm_id) REFERENCES normalized_texts(norm_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_emb_norm ON embedding_records(norm_id);
CREATE INDEX IF NOT EXISTS idx_emb_model ON embedding_records(model_version);

CREATE TABLE IF NOT EXISTS topic_runs (
    run_id TEXT PRIMARY KEY,
    corpus_type TEXT NOT NULL,
    algorithm TEXT NOT NULL,
    n_clusters_requested INTEGER,
    n_clusters_found INTEGER NOT NULL,
    n_noise_points INTEGER NOT NULL DEFAULT 0,
    parameters_json TEXT NOT NULL DEFAULT '{}',
    silhouette_score REAL,
    davies_bouldin_index REAL,
    created_at_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS topic_clusters (
    cluster_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    cluster_index INTEGER NOT NULL,
    topic_label TEXT NOT NULL,
    keywords_json TEXT NOT NULL DEFAULT '[]',
    doc_count INTEGER NOT NULL DEFAULT 0,
    representative_doc_ids_json TEXT NOT NULL DEFAULT '[]',
    intra_cluster_similarity REAL,
    is_noise INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(run_id) REFERENCES topic_runs(run_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_cluster_run ON topic_clusters(run_id);

CREATE TABLE IF NOT EXISTS topic_assignments (
    assignment_id TEXT PRIMARY KEY,
    cluster_id TEXT NOT NULL,
    norm_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    distance_to_centroid REAL,
    membership_score REAL NOT NULL DEFAULT 1.0,
    FOREIGN KEY(cluster_id) REFERENCES topic_clusters(cluster_id) ON DELETE CASCADE,
    FOREIGN KEY(norm_id) REFERENCES normalized_texts(norm_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_assign_cluster ON topic_assignments(cluster_id);
CREATE INDEX IF NOT EXISTS idx_assign_norm ON topic_assignments(norm_id);

CREATE TABLE IF NOT EXISTS cross_source_matches (
    match_link_id TEXT PRIMARY KEY,
    editorial_norm_id TEXT NOT NULL,
    editorial_source_id TEXT NOT NULL,
    commentary_norm_id TEXT NOT NULL,
    commentary_source_id TEXT NOT NULL,
    match_id TEXT,
    similarity_score REAL NOT NULL,
    status TEXT NOT NULL,
    confidence REAL NOT NULL,
    matching_method TEXT NOT NULL,
    evidence_json TEXT NOT NULL DEFAULT '{}',
    created_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_xmatch_status ON cross_source_matches(status);
CREATE INDEX IF NOT EXISTS idx_xmatch_ed ON cross_source_matches(editorial_norm_id);
CREATE INDEX IF NOT EXISTS idx_xmatch_comm ON cross_source_matches(commentary_norm_id);

CREATE TABLE IF NOT EXISTS timeline_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    bucket_label TEXT NOT NULL,
    doc_count INTEGER NOT NULL DEFAULT 0,
    mean_sentiment REAL NOT NULL DEFAULT 0.0,
    sentiment_distribution_json TEXT NOT NULL DEFAULT '{}',
    top_topics_json TEXT NOT NULL DEFAULT '[]',
    top_entities_json TEXT NOT NULL DEFAULT '[]',
    match_events_count INTEGER NOT NULL DEFAULT 0,
    observed_timestamps_count INTEGER NOT NULL DEFAULT 0,
    inferred_timestamps_count INTEGER NOT NULL DEFAULT 0,
    created_at_utc TEXT NOT NULL
);
"""


class SQLiteStorageManager:
    """Encapsulates SQLite interactions with WAL mode and transaction safety."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript(DDL_SCHEMA)
            # Record schema version
            cursor = conn.cursor()
            cursor.execute("SELECT version FROM schema_version WHERE version = ?", (SCHEMA_VERSION,))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO schema_version (version, applied_at_utc) VALUES (?, ?)",
                    (SCHEMA_VERSION, datetime.now(timezone.utc).isoformat()),
                )

    # -------------------------------------------------------------------------
    # Ingestion Run & Provenance Management
    # -------------------------------------------------------------------------
    def record_provenance(self, record: SourceRecord) -> bool:
        """Records a raw harvest audit record. Returns True if inserted, False if already exists."""
        query = """
        INSERT INTO source_records (
            provenance_id, source_name, source_identifier, source_url,
            harvest_timestamp_utc, http_status, content_hash_sha256,
            pipeline_version, license_tag, redistributable
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(content_hash_sha256) DO NOTHING;
        """
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                query,
                (
                    record.provenance_id,
                    record.source_name,
                    record.source_identifier,
                    record.source_url,
                    record.harvest_timestamp_utc.isoformat(),
                    record.http_status,
                    record.content_hash_sha256,
                    record.pipeline_version,
                    record.license_tag,
                    1 if record.redistributable else 0,
                ),
            )
            return cur.rowcount > 0

    def start_ingestion_run(self, source_name: str, run_id: Optional[str] = None) -> IngestionRun:
        if not run_id:
            now_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            uniq = uuid.uuid4().hex[:6]
            run_id = f"run_{source_name}_{now_str}_{uniq}"
        run = IngestionRun(run_id=run_id, source_name=source_name, status="running")
        query = """
        INSERT INTO ingestion_runs (
            run_id, source_name, status, started_at_utc, records_extracted, records_ingested, records_skipped
        ) VALUES (?, ?, ?, ?, 0, 0, 0);
        """
        with self._get_connection() as conn:
            conn.execute(query, (run.run_id, run.source_name, run.status, run.started_at_utc.isoformat()))
        return run

    def update_ingestion_run(self, run: IngestionRun) -> None:
        query = """
        UPDATE ingestion_runs SET
            status = ?,
            completed_at_utc = ?,
            records_extracted = ?,
            records_ingested = ?,
            records_skipped = ?,
            error_message = ?
        WHERE run_id = ?;
        """
        completed = run.completed_at_utc.isoformat() if run.completed_at_utc else datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                query,
                (
                    run.status,
                    completed,
                    run.records_extracted,
                    run.records_ingested,
                    run.records_skipped,
                    run.error_message,
                    run.run_id,
                ),
            )

    # -------------------------------------------------------------------------
    # Teams & Players
    # -------------------------------------------------------------------------
    def upsert_team(self, team: TeamRecord) -> None:
        query = """
        INSERT INTO teams (team_id, name, aliases_json)
        VALUES (?, ?, ?)
        ON CONFLICT(team_id) DO UPDATE SET
            name = excluded.name,
            aliases_json = excluded.aliases_json;
        """
        with self._get_connection() as conn:
            conn.execute(query, (team.team_id, team.name, json.dumps(team.aliases)))

    def upsert_player(self, player: PlayerRecord) -> None:
        query = """
        INSERT INTO players (player_id, full_name, cricsheet_id, primary_team_id, batting_style, bowling_style, aliases_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(player_id) DO UPDATE SET
            full_name = excluded.full_name,
            cricsheet_id = COALESCE(excluded.cricsheet_id, players.cricsheet_id),
            primary_team_id = COALESCE(excluded.primary_team_id, players.primary_team_id),
            batting_style = COALESCE(excluded.batting_style, players.batting_style),
            bowling_style = COALESCE(excluded.bowling_style, players.bowling_style),
            aliases_json = excluded.aliases_json;
        """
        with self._get_connection() as conn:
            conn.execute(
                query,
                (
                    player.player_id,
                    player.full_name,
                    player.cricsheet_id,
                    player.primary_team_id,
                    player.batting_style,
                    player.bowling_style,
                    json.dumps(player.aliases),
                ),
            )

    # -------------------------------------------------------------------------
    # Matches & Deliveries
    # -------------------------------------------------------------------------
    def upsert_match(self, match: MatchRecord) -> None:
        query = """
        INSERT INTO matches (
            match_id, tournament, season, match_date, venue, city, team1_id, team2_id,
            toss_winner_id, toss_decision, winner_id, win_by_runs, win_by_wickets,
            player_of_match_id, target_runs, metadata_json, provenance_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(match_id) DO UPDATE SET
            winner_id = excluded.winner_id,
            win_by_runs = excluded.win_by_runs,
            win_by_wickets = excluded.win_by_wickets,
            target_runs = excluded.target_runs,
            metadata_json = excluded.metadata_json;
        """
        with self._get_connection() as conn:
            conn.execute(
                query,
                (
                    match.match_id,
                    match.tournament,
                    match.season,
                    match.match_date,
                    match.venue,
                    match.city,
                    match.team1_id,
                    match.team2_id,
                    match.toss_winner_id,
                    match.toss_decision,
                    match.winner_id,
                    match.win_by_runs,
                    match.win_by_wickets,
                    match.player_of_match_id,
                    match.target_runs,
                    json.dumps(match.metadata),
                    match.provenance_id,
                ),
            )

    def insert_deliveries_batch(self, deliveries: List[DeliveryRecord]) -> int:
        query = """
        INSERT INTO deliveries (
            delivery_id, match_id, innings, over_num, ball_num, batter_id, bowler_id,
            non_striker_id, batter_runs, extra_runs, extra_type, total_runs,
            is_legal, is_wicket, wicket_kind, player_dismissed_id, phase
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(delivery_id) DO NOTHING;
        """
        rows = [
            (
                d.delivery_id,
                d.match_id,
                d.innings,
                d.over,
                d.ball,
                d.batter_id,
                d.bowler_id,
                d.non_striker_id,
                d.batter_runs,
                d.extra_runs,
                d.extra_type,
                d.total_runs,
                1 if d.is_legal else 0,
                1 if d.is_wicket else 0,
                d.wicket_kind,
                d.player_dismissed_id,
                d.phase.value if isinstance(d.phase, Enum) else str(d.phase),
            )
            for d in deliveries
        ]
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.executemany(query, rows)
            return cur.rowcount

    # -------------------------------------------------------------------------
    # Articles & Paragraphs (with deduplication)
    # -------------------------------------------------------------------------
    def insert_article_with_paragraphs(
        self, article: ArticleRecord, paragraphs: List[ArticleParagraphRecord]
    ) -> Tuple[bool, str]:
        """
        Inserts article and its paragraphs in a single transaction.
        Deduplicates against both canonical_url and raw_content_hash.
        Returns: (inserted: bool, reason_or_article_id: str)
        """
        check_query = """
        SELECT article_id FROM articles
        WHERE canonical_url = ? OR raw_content_hash = ?;
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(check_query, (article.canonical_url, article.raw_content_hash))
            existing = cursor.fetchone()
            if existing:
                return False, f"Duplicate detected: matches article_id {existing['article_id']}"

            art_insert = """
            INSERT INTO articles (
                article_id, canonical_url, headline, author, published_at_utc,
                source_domain, full_text, summary, language, raw_content_hash, provenance_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
            pub_date = article.published_at_utc.isoformat() if article.published_at_utc else None
            cursor.execute(
                art_insert,
                (
                    article.article_id,
                    article.canonical_url,
                    article.headline,
                    article.author,
                    pub_date,
                    article.source_domain,
                    article.full_text,
                    article.summary,
                    article.language,
                    article.raw_content_hash,
                    article.provenance_id,
                ),
            )

            p_insert = """
            INSERT INTO article_paragraphs (
                paragraph_id, article_id, paragraph_index, text, char_count
            ) VALUES (?, ?, ?, ?, ?);
            """
            p_rows = [
                (p.paragraph_id, p.article_id, p.paragraph_index, p.text, p.char_count)
                for p in paragraphs
            ]
            cursor.executemany(p_insert, p_rows)
            return True, article.article_id

    def upsert_article_with_paragraphs(
        self,
        article: ArticleRecord,
        paragraphs: List[ArticleParagraphRecord],
        allow_update: bool = True,
    ) -> Tuple[bool, str, str]:
        """
        Idempotent insertion or update of an article and its paragraphs in a single transaction.
        Distinguishes duplicate content from a legitimate source update.
        Returns: (applied: bool, status_msg: str, article_id: str)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT article_id, raw_content_hash FROM articles WHERE canonical_url = ?",
                (article.canonical_url,),
            )
            existing_url = cursor.fetchone()

            if existing_url:
                existing_id = existing_url["article_id"]
                existing_hash = existing_url["raw_content_hash"]
                if existing_hash == article.raw_content_hash:
                    return False, f"Duplicate: content hash identical for {existing_id}", existing_id

                if not allow_update:
                    return False, f"Duplicate canonical_url for {existing_id} (updates disallowed)", existing_id

                # Legitimate content update for an existing article
                rev_id = f"rev_{existing_id}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
                rev_insert = """
                INSERT INTO article_revisions (
                    revision_id, article_id, revised_at_utc, old_content_hash, new_content_hash, provenance_id
                ) VALUES (?, ?, ?, ?, ?, ?);
                """
                cursor.execute(
                    rev_insert,
                    (
                        rev_id,
                        existing_id,
                        datetime.now(timezone.utc).isoformat(),
                        existing_hash,
                        article.raw_content_hash,
                        article.provenance_id,
                    ),
                )

                art_update = """
                UPDATE articles SET
                    headline = ?,
                    author = ?,
                    published_at_utc = ?,
                    source_domain = ?,
                    full_text = ?,
                    summary = ?,
                    language = ?,
                    raw_content_hash = ?,
                    provenance_id = ?
                WHERE article_id = ?;
                """
                pub_date = article.published_at_utc.isoformat() if article.published_at_utc else None
                cursor.execute(
                    art_update,
                    (
                        article.headline,
                        article.author,
                        pub_date,
                        article.source_domain,
                        article.full_text,
                        article.summary,
                        article.language,
                        article.raw_content_hash,
                        article.provenance_id,
                        existing_id,
                    ),
                )

                cursor.execute("DELETE FROM article_paragraphs WHERE article_id = ?", (existing_id,))
                p_insert = """
                INSERT INTO article_paragraphs (
                    paragraph_id, article_id, paragraph_index, text, char_count
                ) VALUES (?, ?, ?, ?, ?);
                """
                p_rows = [
                    (p.paragraph_id, existing_id, p.paragraph_index, p.text, p.char_count)
                    for p in paragraphs
                ]
                cursor.executemany(p_insert, p_rows)
                return True, f"Updated: revised content applied to {existing_id}", existing_id

            # Canonical URL not yet seen; check for identical content hash under another URL
            cursor.execute(
                "SELECT article_id FROM articles WHERE raw_content_hash = ?",
                (article.raw_content_hash,),
            )
            existing_hash_match = cursor.fetchone()
            if existing_hash_match:
                return (
                    False,
                    f"Duplicate: content hash matches {existing_hash_match['article_id']}",
                    existing_hash_match["article_id"],
                )

            # Brand new article
            inserted, art_id = self.insert_article_with_paragraphs(article, paragraphs)
            return inserted, "Inserted new article", art_id

    # -------------------------------------------------------------------------
    # Commentary Entries
    # -------------------------------------------------------------------------
    def insert_commentary_batch(self, entries: List[CommentaryRecord]) -> int:
        query = """
        INSERT INTO commentary_entries (
            commentary_id, match_id, innings, over_num, ball_num,
            bowler_raw, batter_raw, text, event_tags_json, source_domain,
            harvest_timestamp_utc, provenance_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(commentary_id) DO NOTHING;
        """
        rows = [
            (
                c.commentary_id,
                c.match_id,
                c.innings,
                c.over,
                c.ball,
                c.bowler_raw,
                c.batter_raw,
                c.text,
                json.dumps(c.event_tags),
                c.source_domain,
                c.harvest_timestamp_utc.isoformat(),
                c.provenance_id,
            )
            for c in entries
        ]
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.executemany(query, rows)
            return cur.rowcount

    # -------------------------------------------------------------------------
    # Match Deliveries Replacement (for revised match data)
    # -------------------------------------------------------------------------
    def replace_deliveries_for_match(self, match_id: str, deliveries: List[DeliveryRecord]) -> int:
        """Atomically replaces deliveries for a revised match."""
        del_query = "DELETE FROM deliveries WHERE match_id = ?;"
        insert_query = """
        INSERT INTO deliveries (
            delivery_id, match_id, innings, over_num, ball_num, batter_id, bowler_id,
            non_striker_id, batter_runs, extra_runs, extra_type, total_runs,
            is_legal, is_wicket, wicket_kind, player_dismissed_id, phase
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(delivery_id) DO NOTHING;
        """
        rows = [
            (
                d.delivery_id,
                d.match_id,
                d.innings,
                d.over,
                d.ball,
                d.batter_id,
                d.bowler_id,
                d.non_striker_id,
                d.batter_runs,
                d.extra_runs,
                d.extra_type,
                d.total_runs,
                1 if d.is_legal else 0,
                1 if d.is_wicket else 0,
                d.wicket_kind,
                d.player_dismissed_id,
                d.phase.value if isinstance(d.phase, Enum) else str(d.phase),
            )
            for d in deliveries
        ]
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(del_query, (match_id,))
            cur.executemany(insert_query, rows)
            return cur.rowcount

    # -------------------------------------------------------------------------
    # Event Alignments
    # -------------------------------------------------------------------------
    def insert_alignments(self, alignments: List[EventAlignmentRecord]) -> int:
        query = """
        INSERT INTO event_alignments (
            alignment_id, paragraph_id, match_id, innings,
            over_window_start, over_window_end, confidence_score,
            alignment_method, supporting_evidence_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(alignment_id) DO UPDATE SET
            confidence_score = excluded.confidence_score,
            supporting_evidence_json = excluded.supporting_evidence_json;
        """
        rows = [
            (
                a.alignment_id,
                a.paragraph_id,
                a.match_id,
                a.innings,
                a.over_window_start,
                a.over_window_end,
                a.confidence_score,
                a.alignment_method,
                json.dumps(a.supporting_evidence),
            )
            for a in alignments
        ]
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.executemany(query, rows)
            return cur.rowcount

    # -------------------------------------------------------------------------
    # Discovered URLs and State Machine Operations
    # -------------------------------------------------------------------------
    def record_discovered_urls(self, urls: List[DiscoveredUrlRecord]) -> Tuple[int, int]:
        """
        Idempotently inserts newly discovered URLs.
        Returns: (new_count, existing_count)
        """
        insert_query = """
        INSERT INTO discovered_urls (
            url_id, source_id, raw_url, canonical_url, state, discovered_at_utc,
            attempt_count, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, 0, ?)
        ON CONFLICT(canonical_url) DO NOTHING;
        """
        new_count = 0
        existing_count = 0
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for u in urls:
                cursor.execute(
                    insert_query,
                    (
                        u.url_id,
                        u.source_id,
                        u.raw_url,
                        u.canonical_url,
                        u.state.value if isinstance(u.state, Enum) else str(u.state),
                        u.discovered_at_utc.isoformat(),
                        json.dumps(u.metadata),
                    ),
                )
                if cursor.rowcount > 0:
                    new_count += 1
                else:
                    existing_count += 1
        return new_count, existing_count

    def transition_url_state(
        self,
        url_id: str,
        new_state: ResourceState | str,
        http_status: Optional[int] = None,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None,
        content_hash: Optional[str] = None,
        error_message: Optional[str] = None,
        increment_attempt: bool = False,
    ) -> None:
        """Transitions a URL to a new state with transition validation and audit fields."""
        dest_state = ResourceState(new_state) if isinstance(new_state, str) else new_state

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT state, attempt_count FROM discovered_urls WHERE url_id = ?", (url_id,))
            row = cursor.fetchone()
            if not row:
                raise KeyError(f"URL with id {url_id} not found in discovered_urls")

            curr_state = ResourceState(row["state"])
            validate_transition(curr_state, dest_state)

            now_iso = datetime.now(timezone.utc).isoformat()
            completed_iso = now_iso if dest_state in (ResourceState.INGESTED, ResourceState.SKIPPED, ResourceState.FAILED) else None

            attempt_increment_sql = "attempt_count = attempt_count + 1," if increment_attempt else ""

            update_query = f"""
            UPDATE discovered_urls SET
                state = ?,
                last_attempt_at_utc = ?,
                completed_at_utc = COALESCE(?, completed_at_utc),
                {attempt_increment_sql}
                http_status = COALESCE(?, http_status),
                etag = COALESCE(?, etag),
                last_modified = COALESCE(?, last_modified),
                content_hash = COALESCE(?, content_hash),
                error_message = ?
            WHERE url_id = ?;
            """
            cursor.execute(
                update_query,
                (
                    dest_state.value,
                    now_iso,
                    completed_iso,
                    http_status,
                    etag,
                    last_modified,
                    content_hash,
                    error_message,
                    url_id,
                ),
            )

    def get_urls_by_state(
        self,
        source_id: Optional[str] = None,
        state: Optional[ResourceState] = None,
        limit: Optional[int] = None,
    ) -> List[DiscoveredUrlRecord]:
        """Queries discovered_urls by state and source."""
        conditions = []
        params: List[Any] = []
        if source_id:
            conditions.append("source_id = ?")
            params.append(source_id)
        if state:
            conditions.append("state = ?")
            params.append(state.value if isinstance(state, Enum) else str(state))

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        limit_clause = f"LIMIT {int(limit)}" if limit else ""
        query = f"SELECT * FROM discovered_urls {where_clause} ORDER BY discovered_at_utc ASC {limit_clause};"

        records: List[DiscoveredUrlRecord] = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            for row in cursor.fetchall():
                records.append(
                    DiscoveredUrlRecord(
                        url_id=row["url_id"],
                        source_id=row["source_id"],
                        raw_url=row["raw_url"],
                        canonical_url=row["canonical_url"],
                        state=ResourceState(row["state"]),
                        discovered_at_utc=datetime.fromisoformat(row["discovered_at_utc"]),
                        last_attempt_at_utc=datetime.fromisoformat(row["last_attempt_at_utc"]) if row["last_attempt_at_utc"] else None,
                        completed_at_utc=datetime.fromisoformat(row["completed_at_utc"]) if row["completed_at_utc"] else None,
                        attempt_count=row["attempt_count"],
                        http_status=row["http_status"],
                        etag=row["etag"],
                        last_modified=row["last_modified"],
                        content_hash=row["content_hash"],
                        error_message=row["error_message"],
                        metadata=json.loads(row["metadata_json"] or "{}"),
                    )
                )
        return records

    def get_url_by_canonical(self, canonical_url: str) -> Optional[DiscoveredUrlRecord]:
        """Finds a tracked URL by its canonical URL."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM discovered_urls WHERE canonical_url = ?", (canonical_url,))
            row = cursor.fetchone()
            if not row:
                return None
            return DiscoveredUrlRecord(
                url_id=row["url_id"],
                source_id=row["source_id"],
                raw_url=row["raw_url"],
                canonical_url=row["canonical_url"],
                state=ResourceState(row["state"]),
                discovered_at_utc=datetime.fromisoformat(row["discovered_at_utc"]),
                last_attempt_at_utc=datetime.fromisoformat(row["last_attempt_at_utc"]) if row["last_attempt_at_utc"] else None,
                completed_at_utc=datetime.fromisoformat(row["completed_at_utc"]) if row["completed_at_utc"] else None,
                attempt_count=row["attempt_count"],
                http_status=row["http_status"],
                etag=row["etag"],
                last_modified=row["last_modified"],
                content_hash=row["content_hash"],
                error_message=row["error_message"],
                metadata=json.loads(row["metadata_json"] or "{}"),
            )

    def reset_retryable_urls(self, source_id: Optional[str] = None) -> int:
        """Resets RETRY_PENDING or FAILED URLs back to QUEUED for resumption."""
        params: List[Any] = [ResourceState.QUEUED.value]
        source_filter = ""
        if source_id:
            source_filter = "AND source_id = ?"
            params.append(source_id)

        query = f"""
        UPDATE discovered_urls
        SET state = ?
        WHERE state IN ('RETRY_PENDING', 'FAILED') {source_filter};
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.rowcount

    def get_source_metrics(self, source_id: Optional[str] = None) -> Dict[str, Any]:
        """Aggregates ingestion quality and operational metrics per source."""
        source_filter = "WHERE source_id = ?" if source_id else ""
        params = [source_id] if source_id else []

        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 1. State counts
            state_query = f"""
            SELECT state, COUNT(*) as cnt
            FROM discovered_urls
            {source_filter}
            GROUP BY state;
            """
            cursor.execute(state_query, params)
            state_counts = {row["state"]: row["cnt"] for row in cursor.fetchall()}

            # 2. Total attempts and failures
            agg_query = f"""
            SELECT
                COUNT(*) as total_discovered,
                COALESCE(SUM(attempt_count), 0) as total_attempts,
                COALESCE(SUM(CASE WHEN http_status >= 400 THEN 1 ELSE 0 END), 0) as http_errors,
                COALESCE(SUM(CASE WHEN error_message IS NOT NULL THEN 1 ELSE 0 END), 0) as total_errors
            FROM discovered_urls
            {source_filter};
            """
            cursor.execute(agg_query, params)
            agg = cursor.fetchone()

            # 3. Entity counts
            articles_cnt = cursor.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
            revisions_cnt = cursor.execute("SELECT COUNT(*) FROM article_revisions").fetchone()[0]
            matches_cnt = cursor.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
            deliveries_cnt = cursor.execute("SELECT COUNT(*) FROM deliveries").fetchone()[0]
            commentary_cnt = cursor.execute("SELECT COUNT(*) FROM commentary_entries").fetchone()[0]

            return {
                "source_id": source_id or "all_sources",
                "total_discovered": agg["total_discovered"],
                "total_attempts": agg["total_attempts"],
                "http_errors": agg["http_errors"],
                "total_errors": agg["total_errors"],
                "states": state_counts,
                "ingested": state_counts.get(ResourceState.INGESTED.value, 0),
                "skipped": state_counts.get(ResourceState.SKIPPED.value, 0),
                "failed": state_counts.get(ResourceState.FAILED.value, 0),
                "retry_pending": state_counts.get(ResourceState.RETRY_PENDING.value, 0),
                "queued": state_counts.get(ResourceState.QUEUED.value, 0),
                "articles_stored": articles_cnt,
                "article_revisions": revisions_cnt,
                "matches_stored": matches_cnt,
                "deliveries_stored": deliveries_cnt,
                "commentary_stored": commentary_cnt,
            }

    # -------------------------------------------------------------------------
    # Query Helpers for Verification
    # -------------------------------------------------------------------------
    def get_match_count(self) -> int:
        with self._get_connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]

    def get_delivery_count(self, match_id: Optional[str] = None) -> int:
        with self._get_connection() as conn:
            if match_id:
                return conn.execute("SELECT COUNT(*) FROM deliveries WHERE match_id = ?", (match_id,)).fetchone()[0]
            return conn.execute("SELECT COUNT(*) FROM deliveries").fetchone()[0]

    def get_article_count(self) -> int:
        with self._get_connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]

    def get_commentary_count(self, match_id: Optional[str] = None) -> int:
        with self._get_connection() as conn:
            if match_id:
                return conn.execute("SELECT COUNT(*) FROM commentary_entries WHERE match_id = ?", (match_id,)).fetchone()[0]
            return conn.execute("SELECT COUNT(*) FROM commentary_entries").fetchone()[0]

    # -------------------------------------------------------------------------
    # NLP Processing & Derived Layer Storage
    # -------------------------------------------------------------------------
    def upsert_normalized_text(self, norm: NormalizedTextRecord) -> bool:
        """Idempotently saves or updates a normalized text entry."""
        query = """
        INSERT INTO normalized_texts (
            norm_id, source_type, source_id, original_text, normalized_text,
            char_count, pipeline_version, processed_at_utc
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(norm_id) DO UPDATE SET
            normalized_text = excluded.normalized_text,
            char_count = excluded.char_count,
            processed_at_utc = excluded.processed_at_utc;
        """
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                query,
                (
                    norm.norm_id,
                    norm.source_type,
                    norm.source_id,
                    norm.original_text,
                    norm.normalized_text,
                    norm.char_count,
                    norm.pipeline_version,
                    norm.processed_at_utc.isoformat(),
                ),
            )
            return cur.rowcount > 0

    def upsert_entity_mentions(self, mentions: List[EntityMentionRecord]) -> int:
        """Idempotently stores or updates entity mentions."""
        query = """
        INSERT INTO entity_mentions (
            mention_id, source_type, source_id, entity_type, surface_text,
            start_char, end_char, detection_method, confidence, resolved_id,
            resolution_status, evidence_json, pipeline_version, created_at_utc
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(mention_id) DO UPDATE SET
            resolved_id = excluded.resolved_id,
            resolution_status = excluded.resolution_status,
            confidence = excluded.confidence,
            evidence_json = excluded.evidence_json;
        """
        rows = [
            (
                m.mention_id,
                m.source_type,
                m.source_id,
                m.entity_type.value if hasattr(m.entity_type, "value") else str(m.entity_type),
                m.surface_text,
                m.start_char,
                m.end_char,
                m.detection_method,
                m.confidence,
                m.resolved_id,
                m.resolution_status.value if hasattr(m.resolution_status, "value") else str(m.resolution_status),
                json.dumps(m.evidence),
                m.pipeline_version,
                m.created_at_utc.isoformat(),
            )
            for m in mentions
        ]
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.executemany(query, rows)
            return cur.rowcount

    def upsert_entity_resolutions(self, resolutions: List[EntityResolutionRecord]) -> int:
        """Idempotently stores candidate evaluation records."""
        query = """
        INSERT INTO entity_resolutions (
            resolution_id, mention_id, candidate_id, entity_type, score,
            is_winner, evidence_json, created_at_utc
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(resolution_id) DO UPDATE SET
            score = excluded.score,
            is_winner = excluded.is_winner,
            evidence_json = excluded.evidence_json;
        """
        rows = [
            (
                r.resolution_id,
                r.mention_id,
                r.candidate_id,
                r.entity_type.value if hasattr(r.entity_type, "value") else str(r.entity_type),
                r.score,
                1 if r.is_winner else 0,
                json.dumps(r.evidence),
                r.created_at_utc.isoformat(),
            )
            for r in resolutions
        ]
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.executemany(query, rows)
            return cur.rowcount

    def upsert_sentiment_baselines(self, sentiments: List[SentimentBaselineRecord]) -> int:
        """Idempotently stores sentiment baseline records."""
        query = """
        INSERT INTO sentiment_baselines (
            sentiment_id, source_type, source_id, target_entity_id,
            general_sentiment, event_polarity, framing_score, compound_score,
            evidence_tokens_json, rule_applied, confidence, pipeline_version, created_at_utc
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(sentiment_id) DO UPDATE SET
            general_sentiment = excluded.general_sentiment,
            event_polarity = excluded.event_polarity,
            framing_score = excluded.framing_score,
            compound_score = excluded.compound_score,
            evidence_tokens_json = excluded.evidence_tokens_json,
            confidence = excluded.confidence;
        """
        rows = [
            (
                s.sentiment_id,
                s.source_type,
                s.source_id,
                s.target_entity_id,
                s.general_sentiment.value if hasattr(s.general_sentiment, "value") else str(s.general_sentiment),
                s.event_polarity.value if hasattr(s.event_polarity, "value") else str(s.event_polarity),
                s.framing_score,
                s.compound_score,
                json.dumps(s.evidence_tokens),
                s.rule_applied,
                s.confidence,
                s.pipeline_version,
                s.created_at_utc.isoformat(),
            )
            for s in sentiments
        ]
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.executemany(query, rows)
            return cur.rowcount

    def start_nlp_run(self, run_id: Optional[str] = None) -> NLPRunRecord:
        """Initializes a new NLP execution run audit record."""
        if not run_id:
            now_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            uniq = uuid.uuid4().hex[:6]
            run_id = f"nlp_run_{now_str}_{uniq}"
        run = NLPRunRecord(run_id=run_id, status="running")
        query = """
        INSERT INTO nlp_runs (run_id, status, started_at_utc, records_processed, mentions_extracted, sentiment_scored, errors_json)
        VALUES (?, ?, ?, 0, 0, 0, '[]');
        """
        with self._get_connection() as conn:
            conn.execute(query, (run.run_id, run.status, run.started_at_utc.isoformat()))
        return run

    def update_nlp_run(self, run: NLPRunRecord) -> None:
        """Updates completed NLP run statistics."""
        completed = run.completed_at_utc.isoformat() if run.completed_at_utc else datetime.now(timezone.utc).isoformat()
        query = """
        UPDATE nlp_runs SET
            status = ?,
            completed_at_utc = ?,
            records_processed = ?,
            mentions_extracted = ?,
            sentiment_scored = ?,
            errors_json = ?
        WHERE run_id = ?;
        """
        with self._get_connection() as conn:
            conn.execute(
                query,
                (
                    run.status,
                    completed,
                    run.records_processed,
                    run.mentions_extracted,
                    run.sentiment_scored,
                    json.dumps(run.errors),
                    run.run_id,
                ),
            )

    def get_paragraphs_for_processing(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieves raw article paragraphs for NLP processing."""
        limit_clause = f"LIMIT {int(limit)}" if limit else ""
        query = f"SELECT paragraph_id, article_id, paragraph_index, text, char_count FROM article_paragraphs ORDER BY article_id, paragraph_index {limit_clause};"
        with self._get_connection() as conn:
            return [dict(row) for row in conn.execute(query).fetchall()]

    def get_commentary_for_processing(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieves commentary entries for NLP processing."""
        limit_clause = f"LIMIT {int(limit)}" if limit else ""
        query = f"SELECT commentary_id, match_id, innings, over_num, ball_num, bowler_raw, batter_raw, text FROM commentary_entries ORDER BY match_id, innings, over_num, ball_num {limit_clause};"
        with self._get_connection() as conn:
            return [dict(row) for row in conn.execute(query).fetchall()]

    def get_entity_mentions(
        self,
        source_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        resolved_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """Queries entity mentions with optional filters."""
        conds = []
        params: List[Any] = []
        if source_id:
            conds.append("source_id = ?")
            params.append(source_id)
        if entity_type:
            conds.append("entity_type = ?")
            params.append(entity_type)
        if resolved_only:
            conds.append("resolution_status = 'RESOLVED'")

        where = f"WHERE {' AND '.join(conds)}" if conds else ""
        query = f"SELECT * FROM entity_mentions {where} ORDER BY start_char ASC;"
        with self._get_connection() as conn:
            return [dict(row) for row in conn.execute(query, params).fetchall()]

    def get_nlp_metrics(self) -> Dict[str, Any]:
        """Calculates aggregated metrics across derived NLP tables."""
        with self._get_connection() as conn:
            norm_cnt = conn.execute("SELECT COUNT(*) FROM normalized_texts;").fetchone()[0]
            men_total = conn.execute("SELECT COUNT(*) FROM entity_mentions;").fetchone()[0]
            men_resolved = conn.execute("SELECT COUNT(*) FROM entity_mentions WHERE resolution_status = 'RESOLVED';").fetchone()[0]
            men_ambiguous = conn.execute("SELECT COUNT(*) FROM entity_mentions WHERE resolution_status = 'AMBIGUOUS';").fetchone()[0]
            men_unresolved = conn.execute("SELECT COUNT(*) FROM entity_mentions WHERE resolution_status = 'UNRESOLVED';").fetchone()[0]
            sent_total = conn.execute("SELECT COUNT(*) FROM sentiment_baselines;").fetchone()[0]
            sent_pos = conn.execute("SELECT COUNT(*) FROM sentiment_baselines WHERE general_sentiment = 'POSITIVE';").fetchone()[0]
            sent_neg = conn.execute("SELECT COUNT(*) FROM sentiment_baselines WHERE general_sentiment = 'NEGATIVE';").fetchone()[0]
            sent_neu = conn.execute("SELECT COUNT(*) FROM sentiment_baselines WHERE general_sentiment = 'NEUTRAL';").fetchone()[0]

            return {
                "normalized_texts_count": norm_cnt,
                "total_mentions": men_total,
                "resolved_mentions": men_resolved,
                "ambiguous_mentions": men_ambiguous,
                "unresolved_mentions": men_unresolved,
                "resolution_rate": round(men_resolved / men_total, 3) if men_total > 0 else 0.0,
                "ambiguity_rate": round(men_ambiguous / men_total, 3) if men_total > 0 else 0.0,
                "total_sentiment_records": sent_total,
                "positive_sentiment_count": sent_pos,
                "negative_sentiment_count": sent_neg,
                "neutral_sentiment_count": sent_neu,
            }

    # -------------------------------------------------------------------------
    # Phase 5: Embeddings, Topics & Narrative Intelligence Storage
    # -------------------------------------------------------------------------

    def upsert_embedding_metadata(self, records: List[EmbeddingMetadataRecord]) -> int:
        """Upserts embedding metadata records."""
        if not records:
            return 0
        with self._get_connection() as conn:
            query = """
            INSERT INTO embedding_records (
                embedding_id, norm_id, source_type, source_id, model_version,
                dimension, text_hash, is_test_double, vector_file_path, vector_index, created_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(embedding_id) DO UPDATE SET
                text_hash = excluded.text_hash,
                vector_file_path = excluded.vector_file_path,
                vector_index = excluded.vector_index,
                created_at_utc = excluded.created_at_utc;
            """
            rows = [
                (
                    r.embedding_id,
                    r.norm_id,
                    r.source_type,
                    r.source_id,
                    r.model_version,
                    r.dimension,
                    r.text_hash,
                    1 if r.is_test_double else 0,
                    r.vector_file_path,
                    r.vector_index,
                    r.created_at.isoformat(),
                )
                for r in records
            ]
            conn.executemany(query, rows)
            return len(records)

    def get_embedding_metadata(
        self,
        norm_id: Optional[str] = None,
        model_version: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Queries stored embedding metadata records."""
        conds = []
        params: List[Any] = []
        if norm_id:
            conds.append("norm_id = ?")
            params.append(norm_id)
        if model_version:
            conds.append("model_version = ?")
            params.append(model_version)

        where = f"WHERE {' AND '.join(conds)}" if conds else ""
        query = f"SELECT * FROM embedding_records {where} ORDER BY created_at_utc DESC;"
        with self._get_connection() as conn:
            return [dict(r) for r in conn.execute(query, params).fetchall()]

    def save_topic_run(
        self,
        run: TopicRunRecord,
        clusters: List[TopicClusterRecord],
        assignments: List[TopicAssignmentRecord],
    ) -> None:
        """Transactionally persists a topic clustering run with clusters and document assignments."""
        with self._get_connection() as conn:
            # Insert topic run
            conn.execute(
                """
                INSERT INTO topic_runs (
                    run_id, corpus_type, algorithm, n_clusters_requested,
                    n_clusters_found, n_noise_points, parameters_json,
                    silhouette_score, davies_bouldin_index, created_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    run.run_id,
                    run.corpus_type.value,
                    run.algorithm,
                    run.n_clusters_requested,
                    run.n_clusters_found,
                    run.n_noise_points,
                    run.parameters_json,
                    run.silhouette_score,
                    run.davies_bouldin_index,
                    run.created_at.isoformat(),
                ),
            )

            # Insert clusters
            cluster_rows = [
                (
                    c.cluster_id,
                    c.run_id,
                    c.cluster_index,
                    c.topic_label,
                    json.dumps(c.keywords),
                    c.doc_count,
                    json.dumps(c.representative_doc_ids),
                    c.intra_cluster_similarity,
                    1 if c.is_noise else 0,
                )
                for c in clusters
            ]
            conn.executemany(
                """
                INSERT INTO topic_clusters (
                    cluster_id, run_id, cluster_index, topic_label, keywords_json,
                    doc_count, representative_doc_ids_json, intra_cluster_similarity, is_noise
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                cluster_rows,
            )

            # Insert assignments
            assign_rows = [
                (
                    a.assignment_id,
                    a.cluster_id,
                    a.norm_id,
                    a.source_id,
                    a.distance_to_centroid,
                    a.membership_score,
                )
                for a in assignments
            ]
            conn.executemany(
                """
                INSERT INTO topic_assignments (
                    assignment_id, cluster_id, norm_id, source_id,
                    distance_to_centroid, membership_score
                ) VALUES (?, ?, ?, ?, ?, ?);
                """,
                assign_rows,
            )

    def get_topic_runs(self) -> List[Dict[str, Any]]:
        """Queries all topic discovery runs."""
        with self._get_connection() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM topic_runs ORDER BY created_at_utc DESC;").fetchall()]

    def get_topic_clusters(self, run_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Queries topic clusters, optionally filtering by run_id."""
        query = "SELECT * FROM topic_clusters"
        params: List[Any] = []
        if run_id:
            query += " WHERE run_id = ?"
            params.append(run_id)
        query += " ORDER BY cluster_index ASC;"
        with self._get_connection() as conn:
            return [dict(r) for r in conn.execute(query, params).fetchall()]

    def save_cross_source_matches(self, matches: List[CrossSourceMatchRecord]) -> int:
        """Upserts cross-source narrative-to-commentary similarity matches."""
        if not matches:
            return 0
        with self._get_connection() as conn:
            query = """
            INSERT INTO cross_source_matches (
                match_link_id, editorial_norm_id, editorial_source_id,
                commentary_norm_id, commentary_source_id, match_id,
                similarity_score, status, confidence, matching_method,
                evidence_json, created_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(match_link_id) DO UPDATE SET
                similarity_score = excluded.similarity_score,
                status = excluded.status,
                confidence = excluded.confidence,
                evidence_json = excluded.evidence_json,
                created_at_utc = excluded.created_at_utc;
            """
            rows = [
                (
                    m.match_link_id,
                    m.editorial_norm_id,
                    m.editorial_source_id,
                    m.commentary_norm_id,
                    m.commentary_source_id,
                    m.match_id,
                    m.similarity_score,
                    m.status.value,
                    m.confidence,
                    m.matching_method,
                    json.dumps(m.evidence),
                    m.created_at.isoformat(),
                )
                for m in matches
            ]
            conn.executemany(query, rows)
            return len(matches)

    def get_cross_source_matches(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Queries stored cross-source semantic matches."""
        query = "SELECT * FROM cross_source_matches"
        params: List[Any] = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY confidence DESC;"
        with self._get_connection() as conn:
            return [dict(r) for r in conn.execute(query, params).fetchall()]

    def save_timeline_snapshots(self, snapshots: List[NarrativeTimelinePoint]) -> int:
        """Stores narrative timeline aggregation snapshots."""
        if not snapshots:
            return 0
        with self._get_connection() as conn:
            query = """
            INSERT OR REPLACE INTO timeline_snapshots (
                snapshot_id, bucket_label, doc_count, mean_sentiment,
                sentiment_distribution_json, top_topics_json, top_entities_json,
                match_events_count, observed_timestamps_count, inferred_timestamps_count,
                created_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
            now_iso = datetime.now(timezone.utc).isoformat()
            rows = [
                (
                    f"snap_{uuid.uuid4().hex[:12]}",
                    s.bucket_label,
                    s.doc_count,
                    s.mean_sentiment,
                    json.dumps(s.sentiment_distribution),
                    json.dumps(s.top_topics),
                    json.dumps(s.top_entities),
                    s.match_events_count,
                    s.observed_timestamps_count,
                    s.inferred_timestamps_count,
                    now_iso,
                )
                for s in snapshots
            ]
            conn.executemany(query, rows)
            return len(snapshots)

    def get_timeline_snapshots(self) -> List[Dict[str, Any]]:
        """Retrieves stored narrative timeline points."""
        with self._get_connection() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM timeline_snapshots ORDER BY bucket_label ASC;").fetchall()]

    def get_analysis_metrics(self) -> Dict[str, Any]:
        """Calculates aggregated metrics across Phase 5 analysis tables."""
        with self._get_connection() as conn:
            emb_count = conn.execute("SELECT COUNT(*) FROM embedding_records;").fetchone()[0]
            topic_runs_count = conn.execute("SELECT COUNT(*) FROM topic_runs;").fetchone()[0]
            clusters_count = conn.execute("SELECT COUNT(*) FROM topic_clusters;").fetchone()[0]
            assigned_docs = conn.execute("SELECT COUNT(*) FROM topic_assignments;").fetchone()[0]
            xmatches_total = conn.execute("SELECT COUNT(*) FROM cross_source_matches;").fetchone()[0]
            xmatches_accepted = conn.execute("SELECT COUNT(*) FROM cross_source_matches WHERE status = 'ACCEPTED';").fetchone()[0]
            xmatches_review = conn.execute("SELECT COUNT(*) FROM cross_source_matches WHERE status = 'NEEDS_REVIEW';").fetchone()[0]
            xmatches_unresolved = conn.execute("SELECT COUNT(*) FROM cross_source_matches WHERE status = 'UNRESOLVED';").fetchone()[0]
            timeline_snaps = conn.execute("SELECT COUNT(*) FROM timeline_snapshots;").fetchone()[0]

            return {
                "embedding_records_count": emb_count,
                "topic_runs_count": topic_runs_count,
                "topic_clusters_count": clusters_count,
                "topic_assigned_docs_count": assigned_docs,
                "cross_source_matches_count": xmatches_total,
                "cross_source_accepted_count": xmatches_accepted,
                "cross_source_review_count": xmatches_review,
                "cross_source_unresolved_count": xmatches_unresolved,
                "timeline_snapshots_count": timeline_snaps,
            }

