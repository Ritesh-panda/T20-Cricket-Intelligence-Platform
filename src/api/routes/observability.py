"""API Routes for Provenance, Ingestion Audits, and Pipeline Observability."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple
from fastapi import APIRouter, Depends, Query

from src.api.dependencies import get_storage, pagination_params
from src.api.schemas.common import PaginatedResponse
from src.api.schemas.observability import (
    AnalyticsRunResponse,
    IngestionRunResponse,
    PipelineStatsResponse,
    SourceRecordResponse,
)
from src.storage.sqlite_manager import SQLiteStorageManager

router = APIRouter(prefix="/observability", tags=["Provenance & Pipeline Observability"])


def _parse_ingestion_run(row: Any) -> IngestionRunResponse:
    return IngestionRunResponse(
        run_id=row["run_id"],
        source_name=row["source_name"],
        status=row["status"],
        started_at_utc=row["started_at_utc"],
        completed_at_utc=row["completed_at_utc"],
        records_extracted=int(row["records_extracted"]),
        records_ingested=int(row["records_ingested"]),
        records_skipped=int(row["records_skipped"]),
        error_message=row["error_message"],
    )


def _parse_source_record(row: Any) -> SourceRecordResponse:
    return SourceRecordResponse(
        provenance_id=row["provenance_id"],
        source_name=row["source_name"],
        source_identifier=row["source_identifier"],
        source_url=row["source_url"],
        harvest_timestamp_utc=row["harvest_timestamp_utc"],
        http_status=row["http_status"],
        content_hash_sha256=row["content_hash_sha256"],
        pipeline_version=row["pipeline_version"],
        license_tag=row["license_tag"],
        redistributable=bool(row["redistributable"]),
    )


def _parse_analytics_run(row: Any) -> AnalyticsRunResponse:
    cohorts_raw = row["cohorts_analyzed_json"]
    try:
        cohorts = json.loads(cohorts_raw) if cohorts_raw else []
    except Exception:
        cohorts = []

    warn_raw = row["warnings_json"]
    try:
        warnings = json.loads(warn_raw) if warn_raw else []
    except Exception:
        warnings = []

    return AnalyticsRunResponse(
        run_id=row["run_id"],
        status=row["status"],
        tournament=row["tournament"],
        entity_type=row["entity_type"],
        cohorts_analyzed=cohorts if isinstance(cohorts, list) else [],
        entities_processed=int(row["entities_processed"]),
        valid_apdi_count=int(row["valid_apdi_count"]),
        insufficient_data_count=int(row["insufficient_data_count"]),
        warnings=warnings if isinstance(warnings, list) else [],
        started_at_utc=row["started_at_utc"],
        completed_at_utc=row["completed_at_utc"],
    )


@router.get("/ingestion-runs", response_model=PaginatedResponse[IngestionRunResponse])
def list_ingestion_runs(
    status: Optional[str] = Query(None, description="Filter by status (COMPLETED/FAILED/IN_PROGRESS)"),
    pagination: Tuple[int, int] = Depends(pagination_params),
    storage: SQLiteStorageManager = Depends(get_storage),
) -> PaginatedResponse[IngestionRunResponse]:
    """Retrieves paginated ingestion run execution records and audit statistics."""
    limit, offset = pagination
    where_clauses: List[str] = []
    params: List[Any] = []

    if status:
        where_clauses.append("status = ?")
        params.append(status.upper())

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    with storage._get_connection() as conn:
        count_query = f"SELECT COUNT(*) FROM ingestion_runs {where_sql};"
        total = conn.execute(count_query, params).fetchone()[0]

        query = f"""
            SELECT * FROM ingestion_runs
            {where_sql}
            ORDER BY started_at_utc DESC, run_id ASC
            LIMIT ? OFFSET ?;
        """
        rows = conn.execute(query, params + [limit, offset]).fetchall()
        items = [_parse_ingestion_run(r) for r in rows]

    return PaginatedResponse.create(items=items, total=total, limit=limit, offset=offset)


@router.get("/sources", response_model=PaginatedResponse[SourceRecordResponse])
def list_sources(
    source_name: Optional[str] = Query(None, description="Filter by source identifier"),
    pagination: Tuple[int, int] = Depends(pagination_params),
    storage: SQLiteStorageManager = Depends(get_storage),
) -> PaginatedResponse[SourceRecordResponse]:
    """Retrieves paginated immutable provenance records for crawled/harvested assets."""
    limit, offset = pagination
    where_clauses: List[str] = []
    params: List[Any] = []

    if source_name:
        where_clauses.append("source_name = ?")
        params.append(source_name)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    with storage._get_connection() as conn:
        count_query = f"SELECT COUNT(*) FROM source_records {where_sql};"
        total = conn.execute(count_query, params).fetchone()[0]

        query = f"""
            SELECT provenance_id, source_name, source_identifier, source_url,
                   harvest_timestamp_utc, http_status, content_hash_sha256,
                   pipeline_version, license_tag, redistributable
            FROM source_records
            {where_sql}
            ORDER BY harvest_timestamp_utc DESC, provenance_id ASC
            LIMIT ? OFFSET ?;
        """
        rows = conn.execute(query, params + [limit, offset]).fetchall()
        items = [_parse_source_record(r) for r in rows]

    return PaginatedResponse.create(items=items, total=total, limit=limit, offset=offset)


@router.get("/pipeline-stats", response_model=PipelineStatsResponse)
def get_pipeline_stats(
    source_id: Optional[str] = Query(None, description="Optional source filter (e.g. cricsheet)"),
    storage: SQLiteStorageManager = Depends(get_storage),
) -> PipelineStatsResponse:
    """Retrieves aggregated URL discovery, crawler attempt, and entity counts."""
    metrics = storage.get_source_metrics(source_id)

    return PipelineStatsResponse(
        source_id=source_id or "all",
        total_discovered=metrics.get("total_discovered", 0),
        total_attempts=metrics.get("total_attempts", 0),
        http_errors=metrics.get("http_errors", 0),
        total_errors=metrics.get("total_errors", 0),
        state_distribution=metrics.get("state_distribution", {}),
        entity_counts=metrics.get("entity_counts", {}),
    )


@router.get("/analytics-runs", response_model=PaginatedResponse[AnalyticsRunResponse])
def list_analytics_runs(
    tournament: Optional[str] = Query(None, description="Tournament filter"),
    pagination: Tuple[int, int] = Depends(pagination_params),
    storage: SQLiteStorageManager = Depends(get_storage),
) -> PaginatedResponse[AnalyticsRunResponse]:
    """Retrieves execution audit records for APDI and analytics batches."""
    limit, offset = pagination
    where_clauses: List[str] = []
    params: List[Any] = []

    if tournament:
        where_clauses.append("tournament = ?")
        params.append(tournament)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    with storage._get_connection() as conn:
        count_query = f"SELECT COUNT(*) FROM analytics_runs {where_sql};"
        total = conn.execute(count_query, params).fetchone()[0]

        query = f"""
            SELECT * FROM analytics_runs
            {where_sql}
            ORDER BY started_at_utc DESC, run_id ASC
            LIMIT ? OFFSET ?;
        """
        rows = conn.execute(query, params + [limit, offset]).fetchall()
        items = [_parse_analytics_run(r) for r in rows]

    return PaginatedResponse.create(items=items, total=total, limit=limit, offset=offset)
