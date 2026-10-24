"""API Routes for Topics, Entity Mentions, Timeline Snapshots, and Alignments."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple
from fastapi import APIRouter, Depends, Query

from src.api.dependencies import get_storage, pagination_params
from src.api.errors import ResourceNotFoundError
from src.api.schemas.common import PaginatedResponse
from src.api.schemas.nlp import (
    CrossSourceMatchResponse,
    EntityMentionResponse,
    NarrativeTimelineResponse,
    TopicClusterResponse,
)
from src.storage.sqlite_manager import SQLiteStorageManager

router = APIRouter(tags=["NLP, Topics & Narrative Intelligence"])


def _parse_cluster(row: Any) -> TopicClusterResponse:
    kw_raw = row["keywords_json"]
    try:
        keywords = json.loads(kw_raw) if kw_raw else []
    except Exception:
        keywords = []

    rep_raw = row["representative_doc_ids_json"]
    try:
        rep_ids = json.loads(rep_raw) if rep_raw else []
    except Exception:
        rep_ids = []

    return TopicClusterResponse(
        cluster_id=row["cluster_id"],
        run_id=row["run_id"],
        cluster_index=int(row["cluster_index"]),
        topic_label=row["topic_label"],
        keywords=keywords if isinstance(keywords, list) else [],
        doc_count=int(row["doc_count"]),
        representative_doc_ids=rep_ids if isinstance(rep_ids, list) else [],
        intra_cluster_similarity=row["intra_cluster_similarity"],
        is_noise=bool(row["is_noise"]),
    )


def _parse_mention(row: Any) -> EntityMentionResponse:
    ev_raw = row["evidence_json"]
    try:
        evidence = json.loads(ev_raw) if ev_raw else {}
    except Exception:
        evidence = {}

    return EntityMentionResponse(
        mention_id=row["mention_id"],
        source_type=row["source_type"],
        source_id=row["source_id"],
        entity_type=row["entity_type"],
        surface_text=row["surface_text"],
        start_char=int(row["start_char"]),
        end_char=int(row["end_char"]),
        detection_method=row["detection_method"],
        confidence=float(row["confidence"]),
        resolved_id=row["resolved_id"],
        resolution_status=row["resolution_status"],
        evidence=evidence if isinstance(evidence, dict) else {},
        pipeline_version=row["pipeline_version"],
        created_at_utc=row["created_at_utc"],
    )


def _parse_timeline(row: Any) -> NarrativeTimelineResponse:
    dist_raw = row["sentiment_distribution_json"]
    try:
        dist = json.loads(dist_raw) if dist_raw else {}
    except Exception:
        dist = {}

    top_t_raw = row["top_topics_json"]
    try:
        top_topics = json.loads(top_t_raw) if top_t_raw else []
    except Exception:
        top_topics = []

    top_e_raw = row["top_entities_json"]
    try:
        top_entities = json.loads(top_e_raw) if top_e_raw else []
    except Exception:
        top_entities = []

    return NarrativeTimelineResponse(
        snapshot_id=row["snapshot_id"],
        bucket_label=row["bucket_label"],
        doc_count=int(row["doc_count"]),
        mean_sentiment=float(row["mean_sentiment"]),
        sentiment_distribution=dist if isinstance(dist, dict) else {},
        top_topics=top_topics if isinstance(top_topics, list) else [],
        top_entities=top_entities if isinstance(top_entities, list) else [],
        match_events_count=int(row["match_events_count"]),
        observed_timestamps_count=int(row["observed_timestamps_count"]),
        inferred_timestamps_count=int(row["inferred_timestamps_count"]),
        created_at_utc=row["created_at_utc"],
    )


def _parse_cross_match(row: Any) -> CrossSourceMatchResponse:
    ev_raw = row["evidence_json"]
    try:
        evidence = json.loads(ev_raw) if ev_raw else {}
    except Exception:
        evidence = {}

    return CrossSourceMatchResponse(
        match_link_id=row["match_link_id"],
        editorial_norm_id=row["editorial_norm_id"],
        editorial_source_id=row["editorial_source_id"],
        commentary_norm_id=row["commentary_norm_id"],
        commentary_source_id=row["commentary_source_id"],
        match_id=row["match_id"],
        similarity_score=float(row["similarity_score"]),
        status=row["status"],
        confidence=float(row["confidence"]),
        matching_method=row["matching_method"],
        evidence=evidence if isinstance(evidence, dict) else {},
        created_at_utc=row["created_at_utc"],
    )


# -----------------------------------------------------------------------------
# Topic Endpoints
# -----------------------------------------------------------------------------
@router.get("/topics", response_model=PaginatedResponse[TopicClusterResponse])
def list_topics(
    run_id: Optional[str] = Query(None, description="Filter by topic discovery run identifier"),
    pagination: Tuple[int, int] = Depends(pagination_params),
    storage: SQLiteStorageManager = Depends(get_storage),
) -> PaginatedResponse[TopicClusterResponse]:
    """Retrieves discovered topic clusters with keyword descriptors and representative texts."""
    limit, offset = pagination
    where_clauses: List[str] = []
    params: List[Any] = []

    if run_id:
        where_clauses.append("run_id = ?")
        params.append(run_id)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    with storage._get_connection() as conn:
        count_query = f"SELECT COUNT(*) FROM topic_clusters {where_sql};"
        total = conn.execute(count_query, params).fetchone()[0]

        query = f"""
            SELECT * FROM topic_clusters
            {where_sql}
            ORDER BY cluster_index ASC, cluster_id ASC
            LIMIT ? OFFSET ?;
        """
        rows = conn.execute(query, params + [limit, offset]).fetchall()
        items = [_parse_cluster(r) for r in rows]

    return PaginatedResponse.create(items=items, total=total, limit=limit, offset=offset)


@router.get("/topics/{topic_id}", response_model=TopicClusterResponse)
def get_topic(
    topic_id: str,
    storage: SQLiteStorageManager = Depends(get_storage),
) -> TopicClusterResponse:
    """Retrieves a single topic cluster record or returns 404."""
    with storage._get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM topic_clusters WHERE cluster_id = ?;", (topic_id,)
        ).fetchone()
        if not row:
            raise ResourceNotFoundError("topics", topic_id)
        return _parse_cluster(row)


# -----------------------------------------------------------------------------
# Entity Mention Endpoints
# -----------------------------------------------------------------------------
@router.get("/entities", response_model=PaginatedResponse[EntityMentionResponse])
def list_entity_mentions(
    entity_type: Optional[str] = Query(None, description="Filter by entity type (PLAYER/TEAM)"),
    resolution_status: Optional[str] = Query(
        None, description="Filter by status (RESOLVED/UNRESOLVED/AMBIGUOUS)"
    ),
    resolved_id: Optional[str] = Query(None, description="Filter by canonical resolved ID"),
    source_type: Optional[str] = Query(
        None, description="Filter by source type (article_paragraph/commentary_entry)"
    ),
    pagination: Tuple[int, int] = Depends(pagination_params),
    storage: SQLiteStorageManager = Depends(get_storage),
) -> PaginatedResponse[EntityMentionResponse]:
    """Retrieves fine-grained cricket entity mentions and resolution status."""
    limit, offset = pagination
    where_clauses: List[str] = []
    params: List[Any] = []

    if entity_type:
        where_clauses.append("entity_type = ?")
        params.append(entity_type.upper())
    if resolution_status:
        where_clauses.append("resolution_status = ?")
        params.append(resolution_status.upper())
    if resolved_id:
        where_clauses.append("resolved_id = ?")
        params.append(resolved_id)
    if source_type:
        where_clauses.append("source_type = ?")
        params.append(source_type)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    with storage._get_connection() as conn:
        count_query = f"SELECT COUNT(*) FROM entity_mentions {where_sql};"
        total = conn.execute(count_query, params).fetchone()[0]

        query = f"""
            SELECT * FROM entity_mentions
            {where_sql}
            ORDER BY created_at_utc DESC, mention_id ASC
            LIMIT ? OFFSET ?;
        """
        rows = conn.execute(query, params + [limit, offset]).fetchall()
        items = [_parse_mention(r) for r in rows]

    return PaginatedResponse.create(items=items, total=total, limit=limit, offset=offset)


# -----------------------------------------------------------------------------
# Narrative Intelligence Endpoints
# -----------------------------------------------------------------------------
@router.get("/narratives/timeline", response_model=PaginatedResponse[NarrativeTimelineResponse])
def list_narrative_timeline(
    pagination: Tuple[int, int] = Depends(pagination_params),
    storage: SQLiteStorageManager = Depends(get_storage),
) -> PaginatedResponse[NarrativeTimelineResponse]:
    """Retrieves chronological narrative timeline snapshots with sentiment and topic shifts."""
    limit, offset = pagination

    with storage._get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM timeline_snapshots;").fetchone()[0]

        query = """
            SELECT * FROM timeline_snapshots
            ORDER BY bucket_label ASC, snapshot_id ASC
            LIMIT ? OFFSET ?;
        """
        rows = conn.execute(query, (limit, offset)).fetchall()
        items = [_parse_timeline(r) for r in rows]

    return PaginatedResponse.create(items=items, total=total, limit=limit, offset=offset)


@router.get("/narratives/matches", response_model=PaginatedResponse[CrossSourceMatchResponse])
def list_narrative_matches(
    status: Optional[str] = Query(None, description="Filter by alignment status (ALIGNED/PARTIAL)"),
    match_id: Optional[str] = Query(None, description="Filter by match ID"),
    pagination: Tuple[int, int] = Depends(pagination_params),
    storage: SQLiteStorageManager = Depends(get_storage),
) -> PaginatedResponse[CrossSourceMatchResponse]:
    """Retrieves cross-source alignment links connecting editorial passages to commentary facts."""
    limit, offset = pagination
    where_clauses: List[str] = []
    params: List[Any] = []

    if status:
        where_clauses.append("status = ?")
        params.append(status.upper())
    if match_id:
        where_clauses.append("match_id = ?")
        params.append(match_id)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    with storage._get_connection() as conn:
        count_query = f"SELECT COUNT(*) FROM cross_source_matches {where_sql};"
        total = conn.execute(count_query, params).fetchone()[0]

        query = f"""
            SELECT * FROM cross_source_matches
            {where_sql}
            ORDER BY similarity_score DESC, match_link_id ASC
            LIMIT ? OFFSET ?;
        """
        rows = conn.execute(query, params + [limit, offset]).fetchall()
        items = [_parse_cross_match(r) for r in rows]

    return PaginatedResponse.create(items=items, total=total, limit=limit, offset=offset)
