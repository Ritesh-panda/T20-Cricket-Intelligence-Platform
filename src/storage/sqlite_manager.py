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
from src.analytics.schemas import (
    APDIRecord,
    AnalyticsRunRecord,
    CricketPerformanceMetrics,
    MediaAttentionMetrics,
)

SCHEMA_VERSION = 5

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

CREATE TABLE IF NOT EXISTS attention_metrics (
    metric_id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL,
    entity_name TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    tournament TEXT NOT NULL,
    window_start TEXT,
    window_end TEXT,
    paragraph_count INTEGER NOT NULL DEFAULT 0,
    raw_mention_count INTEGER NOT NULL DEFAULT 0,
    article_reach INTEGER NOT NULL DEFAULT 0,
    source_diversity_count INTEGER NOT NULL DEFAULT 0,
    sources_json TEXT NOT NULL DEFAULT '[]',
    prominence_score REAL NOT NULL DEFAULT 0.0,
    headline_mentions INTEGER NOT NULL DEFAULT 0,
    lead_paragraph_mentions INTEGER NOT NULL DEFAULT 0,
    body_paragraph_mentions INTEGER NOT NULL DEFAULT 0,
    event_linked_mentions INTEGER NOT NULL DEFAULT 0,
    temporal_distribution_json TEXT NOT NULL DEFAULT '{}',
    article_ids_json TEXT NOT NULL DEFAULT '[]',
    paragraph_ids_json TEXT NOT NULL DEFAULT '[]',
    raw_attention_composite REAL NOT NULL DEFAULT 0.0,
    formula_version TEXT NOT NULL,
    created_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_att_entity ON attention_metrics(entity_id);
CREATE INDEX IF NOT EXISTS idx_att_tourn ON attention_metrics(tournament);

CREATE TABLE IF NOT EXISTS performance_metrics (
    metric_id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL,
    entity_name TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    role TEXT NOT NULL,
    tournament TEXT NOT NULL,
    window_start TEXT,
    window_end TEXT,
    matches_played INTEGER NOT NULL DEFAULT 0,
    innings_count INTEGER NOT NULL DEFAULT 0,
    runs_scored INTEGER NOT NULL DEFAULT 0,
    balls_faced INTEGER NOT NULL DEFAULT 0,
    strike_rate REAL,
    fours INTEGER NOT NULL DEFAULT 0,
    sixes INTEGER NOT NULL DEFAULT 0,
    dismissals INTEGER NOT NULL DEFAULT 0,
    batting_average REAL,
    legal_balls_bowled INTEGER NOT NULL DEFAULT 0,
    overs_bowled REAL NOT NULL DEFAULT 0.0,
    runs_conceded INTEGER NOT NULL DEFAULT 0,
    wickets_taken INTEGER NOT NULL DEFAULT 0,
    bowling_economy REAL,
    bowling_average REAL,
    bowling_strike_rate REAL,
    wides_conceded INTEGER NOT NULL DEFAULT 0,
    noballs_conceded INTEGER NOT NULL DEFAULT 0,
    powerplay_runs INTEGER NOT NULL DEFAULT 0,
    powerplay_balls INTEGER NOT NULL DEFAULT 0,
    powerplay_wickets INTEGER NOT NULL DEFAULT 0,
    death_runs INTEGER NOT NULL DEFAULT 0,
    death_balls INTEGER NOT NULL DEFAULT 0,
    death_wickets INTEGER NOT NULL DEFAULT 0,
    team_wins INTEGER NOT NULL DEFAULT 0,
    team_matches INTEGER NOT NULL DEFAULT 0,
    win_percentage REAL,
    raw_performance_composite REAL NOT NULL DEFAULT 0.0,
    match_ids_json TEXT NOT NULL DEFAULT '[]',
    raw_stats_json TEXT NOT NULL DEFAULT '{}',
    formula_version TEXT NOT NULL,
    created_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_perf_entity ON performance_metrics(entity_id);
CREATE INDEX IF NOT EXISTS idx_perf_role ON performance_metrics(role);
CREATE INDEX IF NOT EXISTS idx_perf_tourn ON performance_metrics(tournament);

CREATE TABLE IF NOT EXISTS apdi_records (
    record_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    entity_name TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    role_cohort TEXT NOT NULL,
    tournament TEXT NOT NULL,
    comparison_window TEXT NOT NULL,
    raw_attention_score REAL NOT NULL,
    normalized_attention_score REAL,
    raw_performance_score REAL NOT NULL,
    normalized_performance_score REAL,
    apdi_value REAL,
    discrepancy_category TEXT NOT NULL,
    evidence_sufficiency_status TEXT NOT NULL,
    sample_size_indicators_json TEXT NOT NULL DEFAULT '{}',
    data_quality_warnings_json TEXT NOT NULL DEFAULT '[]',
    framing_breakdown_json TEXT NOT NULL DEFAULT '{}',
    evidence_lineage_json TEXT NOT NULL DEFAULT '{}',
    formula_version TEXT NOT NULL,
    created_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_apdi_run ON apdi_records(run_id);
CREATE INDEX IF NOT EXISTS idx_apdi_entity ON apdi_records(entity_id);
CREATE INDEX IF NOT EXISTS idx_apdi_cohort ON apdi_records(role_cohort);
CREATE INDEX IF NOT EXISTS idx_apdi_cat ON apdi_records(discrepancy_category);

CREATE TABLE IF NOT EXISTS analytics_runs (
    run_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    tournament TEXT NOT NULL,
    entity_type TEXT,
    cohorts_analyzed_json TEXT NOT NULL DEFAULT '[]',
    entities_processed INTEGER NOT NULL DEFAULT 0,
    valid_apdi_count INTEGER NOT NULL DEFAULT 0,
    insufficient_data_count INTEGER NOT NULL DEFAULT 0,
    warnings_json TEXT NOT NULL DEFAULT '[]',
    started_at_utc TEXT NOT NULL,
    completed_at_utc TEXT
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

    # -------------------------------------------------------------------------
    # Phase 6A: Analytics Persistence & Retrieval
    # -------------------------------------------------------------------------
    def upsert_attention_metrics(self, record: MediaAttentionMetrics) -> bool:
        """Idempotently saves or updates media attention metrics for an entity."""
        query = """
        INSERT INTO attention_metrics (
            metric_id, entity_id, entity_name, entity_type, tournament,
            window_start, window_end, paragraph_count, raw_mention_count,
            article_reach, source_diversity_count, sources_json,
            prominence_score, headline_mentions, lead_paragraph_mentions,
            body_paragraph_mentions, event_linked_mentions,
            temporal_distribution_json, article_ids_json, paragraph_ids_json,
            raw_attention_composite, formula_version, created_at_utc
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(metric_id) DO UPDATE SET
            paragraph_count = excluded.paragraph_count,
            raw_mention_count = excluded.raw_mention_count,
            article_reach = excluded.article_reach,
            source_diversity_count = excluded.source_diversity_count,
            sources_json = excluded.sources_json,
            prominence_score = excluded.prominence_score,
            headline_mentions = excluded.headline_mentions,
            lead_paragraph_mentions = excluded.lead_paragraph_mentions,
            body_paragraph_mentions = excluded.body_paragraph_mentions,
            event_linked_mentions = excluded.event_linked_mentions,
            temporal_distribution_json = excluded.temporal_distribution_json,
            article_ids_json = excluded.article_ids_json,
            paragraph_ids_json = excluded.paragraph_ids_json,
            raw_attention_composite = excluded.raw_attention_composite,
            formula_version = excluded.formula_version,
            created_at_utc = excluded.created_at_utc;
        """
        with self._get_connection() as conn:
            conn.execute(
                query,
                (
                    record.metric_id,
                    record.entity_id,
                    record.entity_name,
                    record.entity_type,
                    record.tournament,
                    record.window_start,
                    record.window_end,
                    record.paragraph_count,
                    record.raw_mention_count,
                    record.article_reach,
                    record.source_diversity_count,
                    json.dumps(record.sources),
                    record.prominence_score,
                    record.headline_mentions,
                    record.lead_paragraph_mentions,
                    record.body_paragraph_mentions,
                    record.event_linked_mentions,
                    json.dumps(record.temporal_distribution),
                    json.dumps(record.article_ids),
                    json.dumps(record.paragraph_ids),
                    record.raw_attention_composite,
                    record.formula_version,
                    record.created_at_utc.isoformat(),
                ),
            )
            return True

    def get_attention_metrics(self, entity_id: str, tournament: str = "T20 World Cup 2024") -> Optional[Dict[str, Any]]:
        """Retrieves stored attention metrics for an entity."""
        query = "SELECT * FROM attention_metrics WHERE entity_id = ? AND tournament = ?;"
        with self._get_connection() as conn:
            row = conn.execute(query, (entity_id, tournament)).fetchone()
            if not row:
                return None
            d = dict(row)
            d["sources"] = json.loads(d.get("sources_json") or "[]")
            d["temporal_distribution"] = json.loads(d.get("temporal_distribution_json") or "{}")
            d["article_ids"] = json.loads(d.get("article_ids_json") or "[]")
            d["paragraph_ids"] = json.loads(d.get("paragraph_ids_json") or "[]")
            return d

    def get_all_attention_metrics(self, tournament: str = "T20 World Cup 2024") -> List[Dict[str, Any]]:
        """Retrieves all stored attention metrics for a tournament."""
        query = "SELECT * FROM attention_metrics WHERE tournament = ? ORDER BY raw_attention_composite DESC;"
        with self._get_connection() as conn:
            rows = conn.execute(query, (tournament,)).fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["sources"] = json.loads(d.get("sources_json") or "[]")
                d["temporal_distribution"] = json.loads(d.get("temporal_distribution_json") or "{}")
                d["article_ids"] = json.loads(d.get("article_ids_json") or "[]")
                d["paragraph_ids"] = json.loads(d.get("paragraph_ids_json") or "[]")
                results.append(d)
            return results

    def upsert_performance_metrics(self, record: CricketPerformanceMetrics) -> bool:
        """Idempotently saves or updates cricket performance metrics."""
        query = """
        INSERT INTO performance_metrics (
            metric_id, entity_id, entity_name, entity_type, role, tournament,
            window_start, window_end, matches_played, innings_count, runs_scored,
            balls_faced, strike_rate, fours, sixes, dismissals, batting_average,
            legal_balls_bowled, overs_bowled, runs_conceded, wickets_taken,
            bowling_economy, bowling_average, bowling_strike_rate,
            wides_conceded, noballs_conceded, powerplay_runs, powerplay_balls,
            powerplay_wickets, death_runs, death_balls, death_wickets,
            team_wins, team_matches, win_percentage, raw_performance_composite,
            match_ids_json, raw_stats_json, formula_version, created_at_utc
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(metric_id) DO UPDATE SET
            matches_played = excluded.matches_played,
            innings_count = excluded.innings_count,
            runs_scored = excluded.runs_scored,
            balls_faced = excluded.balls_faced,
            strike_rate = excluded.strike_rate,
            fours = excluded.fours,
            sixes = excluded.sixes,
            dismissals = excluded.dismissals,
            batting_average = excluded.batting_average,
            legal_balls_bowled = excluded.legal_balls_bowled,
            overs_bowled = excluded.overs_bowled,
            runs_conceded = excluded.runs_conceded,
            wickets_taken = excluded.wickets_taken,
            bowling_economy = excluded.bowling_economy,
            bowling_average = excluded.bowling_average,
            bowling_strike_rate = excluded.bowling_strike_rate,
            wides_conceded = excluded.wides_conceded,
            noballs_conceded = excluded.noballs_conceded,
            powerplay_runs = excluded.powerplay_runs,
            powerplay_balls = excluded.powerplay_balls,
            powerplay_wickets = excluded.powerplay_wickets,
            death_runs = excluded.death_runs,
            death_balls = excluded.death_balls,
            death_wickets = excluded.death_wickets,
            team_wins = excluded.team_wins,
            team_matches = excluded.team_matches,
            win_percentage = excluded.win_percentage,
            raw_performance_composite = excluded.raw_performance_composite,
            match_ids_json = excluded.match_ids_json,
            raw_stats_json = excluded.raw_stats_json,
            formula_version = excluded.formula_version,
            created_at_utc = excluded.created_at_utc;
        """
        with self._get_connection() as conn:
            conn.execute(
                query,
                (
                    record.metric_id,
                    record.entity_id,
                    record.entity_name,
                    record.entity_type,
                    record.role.value if hasattr(record.role, "value") else str(record.role),
                    record.tournament,
                    record.window_start,
                    record.window_end,
                    record.matches_played,
                    record.innings_count,
                    record.runs_scored,
                    record.balls_faced,
                    record.strike_rate,
                    record.fours,
                    record.sixes,
                    record.dismissals,
                    record.batting_average,
                    record.legal_balls_bowled,
                    record.overs_bowled,
                    record.runs_conceded,
                    record.wickets_taken,
                    record.bowling_economy,
                    record.bowling_average,
                    record.bowling_strike_rate,
                    record.wides_conceded,
                    record.noballs_conceded,
                    record.powerplay_runs,
                    record.powerplay_balls,
                    record.powerplay_wickets,
                    record.death_runs,
                    record.death_balls,
                    record.death_wickets,
                    record.team_wins,
                    record.team_matches,
                    record.win_percentage,
                    record.raw_performance_composite,
                    json.dumps(record.match_ids),
                    record.raw_stats_json,
                    record.formula_version,
                    record.created_at_utc.isoformat(),
                ),
            )
            return True

    def get_performance_metrics(
        self, entity_id: str, role: Optional[str] = None, tournament: str = "T20 World Cup 2024"
    ) -> Optional[Dict[str, Any]]:
        """Retrieves stored performance metrics for an entity."""
        if role:
            query = "SELECT * FROM performance_metrics WHERE entity_id = ? AND role = ? AND tournament = ?;"
            params = (entity_id, role, tournament)
        else:
            query = "SELECT * FROM performance_metrics WHERE entity_id = ? AND tournament = ?;"
            params = (entity_id, tournament)

        with self._get_connection() as conn:
            row = conn.execute(query, params).fetchone()
            if not row:
                return None
            d = dict(row)
            d["match_ids"] = json.loads(d.get("match_ids_json") or "[]")
            d["raw_stats"] = json.loads(d.get("raw_stats_json") or "{}")
            return d

    def get_all_performance_metrics(
        self, role: Optional[str] = None, tournament: str = "T20 World Cup 2024"
    ) -> List[Dict[str, Any]]:
        """Retrieves all stored performance metrics for a cohort and tournament."""
        if role:
            query = "SELECT * FROM performance_metrics WHERE role = ? AND tournament = ? ORDER BY raw_performance_composite DESC;"
            params = (role, tournament)
        else:
            query = "SELECT * FROM performance_metrics WHERE tournament = ? ORDER BY raw_performance_composite DESC;"
            params = (tournament,)

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["match_ids"] = json.loads(d.get("match_ids_json") or "[]")
                d["raw_stats"] = json.loads(d.get("raw_stats_json") or "{}")
                results.append(d)
            return results

    def save_apdi_records(self, records: List[APDIRecord]) -> int:
        """Persists a batch of APDI records transactionally."""
        if not records:
            return 0

        query = """
        INSERT INTO apdi_records (
            record_id, run_id, entity_id, entity_name, entity_type,
            role_cohort, tournament, comparison_window, raw_attention_score,
            normalized_attention_score, raw_performance_score,
            normalized_performance_score, apdi_value, discrepancy_category,
            evidence_sufficiency_status, sample_size_indicators_json,
            data_quality_warnings_json, framing_breakdown_json,
            evidence_lineage_json, formula_version, created_at_utc
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(record_id) DO UPDATE SET
            normalized_attention_score = excluded.normalized_attention_score,
            normalized_performance_score = excluded.normalized_performance_score,
            apdi_value = excluded.apdi_value,
            discrepancy_category = excluded.discrepancy_category,
            evidence_sufficiency_status = excluded.evidence_sufficiency_status,
            sample_size_indicators_json = excluded.sample_size_indicators_json,
            data_quality_warnings_json = excluded.data_quality_warnings_json,
            framing_breakdown_json = excluded.framing_breakdown_json,
            evidence_lineage_json = excluded.evidence_lineage_json,
            formula_version = excluded.formula_version,
            created_at_utc = excluded.created_at_utc;
        """
        rows = [
            (
                r.record_id,
                r.run_id,
                r.entity_id,
                r.entity_name,
                r.entity_type,
                r.role_cohort.value if hasattr(r.role_cohort, "value") else str(r.role_cohort),
                r.tournament,
                r.comparison_window,
                r.raw_attention_score,
                r.normalized_attention_score,
                r.raw_performance_score,
                r.normalized_performance_score,
                r.apdi_value,
                r.discrepancy_category.value if hasattr(r.discrepancy_category, "value") else str(r.discrepancy_category),
                r.evidence_sufficiency_status.value if hasattr(r.evidence_sufficiency_status, "value") else str(r.evidence_sufficiency_status),
                json.dumps(r.sample_size_indicators),
                json.dumps(r.data_quality_warnings),
                json.dumps(r.framing_breakdown),
                json.dumps(r.evidence_lineage),
                r.formula_version,
                r.created_at_utc.isoformat(),
            )
            for r in records
        ]

        with self._get_connection() as conn:
            conn.executemany(query, rows)
            return len(records)

    def get_apdi_records(
        self,
        run_id: Optional[str] = None,
        tournament: Optional[str] = None,
        entity_id: Optional[str] = None,
        role_cohort: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieves stored APDI records matching optional filters."""
        query = "SELECT * FROM apdi_records WHERE 1=1"
        params: List[Any] = []

        if run_id:
            query += " AND run_id = ?"
            params.append(run_id)
        if tournament:
            query += " AND tournament = ?"
            params.append(tournament)
        if entity_id:
            query += " AND entity_id = ?"
            params.append(entity_id)
        if role_cohort:
            query += " AND role_cohort = ?"
            params.append(role_cohort)

        query += " ORDER BY apdi_value DESC NULLS LAST;"

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["sample_size_indicators"] = json.loads(d.get("sample_size_indicators_json") or "{}")
                d["data_quality_warnings"] = json.loads(d.get("data_quality_warnings_json") or "[]")
                d["framing_breakdown"] = json.loads(d.get("framing_breakdown_json") or "{}")
                d["evidence_lineage"] = json.loads(d.get("evidence_lineage_json") or "{}")
                results.append(d)
            return results

    def record_analytics_run(self, record: AnalyticsRunRecord) -> bool:
        """Persists metadata for an analytical execution run."""
        query = """
        INSERT INTO analytics_runs (
            run_id, status, tournament, entity_type, cohorts_analyzed_json,
            entities_processed, valid_apdi_count, insufficient_data_count,
            warnings_json, started_at_utc, completed_at_utc
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(run_id) DO UPDATE SET
            status = excluded.status,
            entities_processed = excluded.entities_processed,
            valid_apdi_count = excluded.valid_apdi_count,
            insufficient_data_count = excluded.insufficient_data_count,
            warnings_json = excluded.warnings_json,
            completed_at_utc = excluded.completed_at_utc;
        """
        with self._get_connection() as conn:
            conn.execute(
                query,
                (
                    record.run_id,
                    record.status,
                    record.tournament,
                    record.entity_type,
                    json.dumps(record.cohorts_analyzed),
                    record.entities_processed,
                    record.valid_apdi_count,
                    record.insufficient_data_count,
                    json.dumps(record.warnings),
                    record.started_at_utc.isoformat(),
                    record.completed_at_utc.isoformat() if record.completed_at_utc else None,
                ),
            )
            return True

    def get_analytics_summary(self, tournament: Optional[str] = None) -> Dict[str, Any]:
        """Provides summary metrics across Phase 6A analytics tables."""
        with self._get_connection() as conn:
            target_tourn = tournament
            if target_tourn:
                chk = conn.execute("SELECT COUNT(*) FROM apdi_records WHERE tournament = ?;", (target_tourn,)).fetchone()[0]
                if chk == 0:
                    alias_row = conn.execute(
                        """
                        SELECT tournament FROM matches 
                        WHERE tournament LIKE ? OR ? LIKE ('%' || tournament || '%')
                        LIMIT 1;
                        """,
                        (f"%{target_tourn.replace('2024', '').strip()}%", target_tourn),
                    ).fetchone()
                    if not alias_row:
                        alias_row = conn.execute(
                            """
                            SELECT tournament FROM apdi_records 
                            WHERE tournament LIKE ? OR ? LIKE ('%' || tournament || '%')
                            LIMIT 1;
                            """,
                            (f"%{target_tourn.replace('2024', '').strip()}%", target_tourn),
                        ).fetchone()
                    if alias_row:
                        target_tourn = alias_row[0]

            if target_tourn:
                att_count = conn.execute("SELECT COUNT(*) FROM attention_metrics WHERE tournament = ?;", (target_tourn,)).fetchone()[0]
                perf_count = conn.execute("SELECT COUNT(*) FROM performance_metrics WHERE tournament = ?;", (target_tourn,)).fetchone()[0]
                apdi_count = conn.execute("SELECT COUNT(*) FROM apdi_records WHERE tournament = ?;", (target_tourn,)).fetchone()[0]
                over_count = conn.execute("SELECT COUNT(*) FROM apdi_records WHERE tournament = ? AND discrepancy_category = 'OVER_ATTENDED';", (target_tourn,)).fetchone()[0]
                under_count = conn.execute("SELECT COUNT(*) FROM apdi_records WHERE tournament = ? AND discrepancy_category = 'UNDER_ATTENDED';", (target_tourn,)).fetchone()[0]
                bal_count = conn.execute("SELECT COUNT(*) FROM apdi_records WHERE tournament = ? AND discrepancy_category = 'BALANCED';", (target_tourn,)).fetchone()[0]
                ins_count = conn.execute("SELECT COUNT(*) FROM apdi_records WHERE tournament = ? AND discrepancy_category = 'INSUFFICIENT_DATA';", (target_tourn,)).fetchone()[0]
            else:
                att_count = conn.execute("SELECT COUNT(*) FROM attention_metrics;").fetchone()[0]
                perf_count = conn.execute("SELECT COUNT(*) FROM performance_metrics;").fetchone()[0]
                apdi_count = conn.execute("SELECT COUNT(*) FROM apdi_records;").fetchone()[0]
                over_count = conn.execute("SELECT COUNT(*) FROM apdi_records WHERE discrepancy_category = 'OVER_ATTENDED';").fetchone()[0]
                under_count = conn.execute("SELECT COUNT(*) FROM apdi_records WHERE discrepancy_category = 'UNDER_ATTENDED';").fetchone()[0]
                bal_count = conn.execute("SELECT COUNT(*) FROM apdi_records WHERE discrepancy_category = 'BALANCED';").fetchone()[0]
                ins_count = conn.execute("SELECT COUNT(*) FROM apdi_records WHERE discrepancy_category = 'INSUFFICIENT_DATA';").fetchone()[0]

            runs_count = conn.execute("SELECT COUNT(*) FROM analytics_runs;").fetchone()[0]

            return {
                "tournament": target_tourn or tournament or "all",
                "attention_metrics_count": att_count,
                "performance_metrics_count": perf_count,
                "apdi_records_count": apdi_count,
                "over_attended_count": over_count,
                "under_attended_count": under_count,
                "balanced_count": bal_count,
                "insufficient_data_count": ins_count,
                "analytics_runs_count": runs_count,
            }


