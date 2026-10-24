"""Health, System Readiness, and Research Status Endpoints."""

from __future__ import annotations

import logging
from typing import Tuple
from fastapi import APIRouter, Depends, Query

from src.api.config import settings
from src.api.dependencies import get_preflight, get_storage
from src.api.schemas.common import HealthResponse, ReadinessResponse, StatusResponse
from src.analytics.preflight import AnalyticsPreflight
from src.storage.sqlite_manager import SQLiteStorageManager

logger = logging.getLogger("routes_health")

router = APIRouter(tags=["Health & System Readiness"])


@router.get("/health", response_model=HealthResponse, summary="Application liveness probe")
def get_health() -> HealthResponse:
    """Verifies that the API service process is alive and responsive."""
    return HealthResponse(
        status="healthy",
        version=settings.api_version,
    )


@router.get("/ready", response_model=ReadinessResponse, summary="Application readiness probe")
def get_readiness(storage: SQLiteStorageManager = Depends(get_storage)) -> ReadinessResponse:
    """Verifies that the database and required underlying persistence are accessible."""
    try:
        with storage._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1;")
            row = cur.fetchone()
            schema_ver = row[0] if row else None

            cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
            tables_count = cur.fetchone()[0]

            return ReadinessResponse(
                status="ready",
                database_accessible=True,
                schema_version=schema_ver,
                database_tables_count=tables_count,
            )
    except Exception as exc:
        logger.warning(f"Readiness check failed: {exc}")
        return ReadinessResponse(
            status="not_ready",
            database_accessible=False,
            schema_version=None,
            database_tables_count=0,
        )


@router.get(
    "/api/v1/status",
    response_model=StatusResponse,
    summary="Research pipeline and analytical data availability status",
)
def get_system_status(
    tournament: str = Query(default=settings.default_tournament, description="Tournament scope"),
    preflight: AnalyticsPreflight = Depends(get_preflight),
) -> StatusResponse:
    """Exposes data inventory, pipeline capability readiness, and whether analytical evidence is sufficient."""
    result = preflight.run_preflight(tournament=tournament)

    record_counts = {
        "matches": result.matches_count,
        "deliveries": result.deliveries_count,
        "articles": result.articles_count,
        "paragraphs": result.paragraphs_count,
        "commentary_entries": result.commentary_count,
        "entity_mentions": result.mentions_count,
        "resolved_mentions": result.resolved_mentions_count,
        "sentiment_baselines": result.sentiment_records_count,
        "eligible_batters": result.eligible_batters_count,
        "eligible_bowlers": result.eligible_bowlers_count,
        "eligible_teams": result.eligible_teams_count,
    }

    pipeline_status = "operational" if result.is_eligible else ("empty" if result.matches_count == 0 and result.articles_count == 0 else "insufficient_data")

    supported_caps = [
        "canonical_schemas",
        "provenance_tracking",
        "cricket_ner_gazetteers",
        "lexicon_sentiment_analysis",
        "semantic_embeddings",
        "topic_discovery",
        "cross_source_event_alignment",
        "media_attention_profiling",
        "objective_performance_scoring",
        "apdi_discrepancy_analysis",
        "rest_api_serving",
    ]

    return StatusResponse(
        pipeline_status=pipeline_status,
        tournament=tournament,
        record_counts=record_counts,
        data_sufficiency_status=result.status.value,
        is_analytics_ready=result.is_eligible,
        supported_capabilities=supported_caps,
        warnings=result.warnings,
        checked_at_utc=result.checked_at_utc,
    )
