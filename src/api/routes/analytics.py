"""API Routes for Phase 6A/6B Media Attention, Cricket Performance, and APDI Analytics."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple
from fastapi import APIRouter, Depends, Query

from src.analytics.framing import NarrativeFramingCalculator
from src.analytics.preflight import AnalyticsPreflight
from src.api.dependencies import (
    get_framing_calculator,
    get_preflight,
    get_storage,
    pagination_params,
)
from src.api.errors import ResourceNotFoundError
from src.api.schemas.analytics import (
    AnalyticsOverviewResponse,
    AnalyticsValidationResponse,
    APDIRecordResponse,
    CricketPerformanceResponse,
    MediaAttentionResponse,
    NarrativeFramingResponse,
)
from src.api.schemas.common import PaginatedResponse
from src.storage.sqlite_manager import SQLiteStorageManager

router = APIRouter(prefix="/analytics", tags=["Analytics & APDI"])


def _parse_attention_row(row: Any) -> MediaAttentionResponse:
    def _loads_list(raw: Any) -> List[Any]:
        try:
            val = json.loads(raw) if raw else []
            return val if isinstance(val, list) else []
        except Exception:
            return []

    def _loads_dict(raw: Any) -> Dict[str, Any]:
        try:
            val = json.loads(raw) if raw else {}
            return val if isinstance(val, dict) else {}
        except Exception:
            return {}

    return MediaAttentionResponse(
        metric_id=row["metric_id"],
        entity_id=row["entity_id"],
        entity_name=row["entity_name"],
        entity_type=row["entity_type"],
        tournament=row["tournament"],
        window_start=row["window_start"],
        window_end=row["window_end"],
        paragraph_count=int(row["paragraph_count"]),
        raw_mention_count=int(row["raw_mention_count"]),
        article_reach=int(row["article_reach"]),
        source_diversity_count=int(row["source_diversity_count"]),
        sources=_loads_list(row["sources_json"]),
        prominence_score=float(row["prominence_score"]),
        headline_mentions=int(row["headline_mentions"]),
        lead_paragraph_mentions=int(row["lead_paragraph_mentions"]),
        body_paragraph_mentions=int(row["body_paragraph_mentions"]),
        event_linked_mentions=int(row["event_linked_mentions"]),
        temporal_distribution=_loads_dict(row["temporal_distribution_json"]),
        article_ids=_loads_list(row["article_ids_json"]),
        paragraph_ids=_loads_list(row["paragraph_ids_json"]),
        raw_attention_composite=float(row["raw_attention_composite"]),
        formula_version=row["formula_version"],
        created_at_utc=row["created_at_utc"],
    )


def _parse_performance_row(row: Any) -> CricketPerformanceResponse:
    def _loads_list(raw: Any) -> List[Any]:
        try:
            val = json.loads(raw) if raw else []
            return val if isinstance(val, list) else []
        except Exception:
            return []

    def _loads_dict(raw: Any) -> Dict[str, Any]:
        try:
            val = json.loads(raw) if raw else {}
            return val if isinstance(val, dict) else {}
        except Exception:
            return {}

    return CricketPerformanceResponse(
        metric_id=row["metric_id"],
        entity_id=row["entity_id"],
        entity_name=row["entity_name"],
        entity_type=row["entity_type"],
        role=row["role"],
        tournament=row["tournament"],
        window_start=row["window_start"],
        window_end=row["window_end"],
        matches_played=int(row["matches_played"]),
        innings_count=int(row["innings_count"]),
        runs_scored=int(row["runs_scored"]),
        balls_faced=int(row["balls_faced"]),
        strike_rate=float(row["strike_rate"]) if row["strike_rate"] is not None else None,
        fours=int(row["fours"]),
        sixes=int(row["sixes"]),
        dismissals=int(row["dismissals"]),
        batting_average=float(row["batting_average"]) if row["batting_average"] is not None else None,
        legal_balls_bowled=int(row["legal_balls_bowled"]),
        overs_bowled=float(row["overs_bowled"]),
        runs_conceded=int(row["runs_conceded"]),
        wickets_taken=int(row["wickets_taken"]),
        bowling_economy=float(row["bowling_economy"]) if row["bowling_economy"] is not None else None,
        bowling_average=float(row["bowling_average"]) if row["bowling_average"] is not None else None,
        bowling_strike_rate=float(row["bowling_strike_rate"]) if row["bowling_strike_rate"] is not None else None,
        wides_conceded=int(row["wides_conceded"]),
        noballs_conceded=int(row["noballs_conceded"]),
        powerplay_runs=int(row["powerplay_runs"]),
        powerplay_balls=int(row["powerplay_balls"]),
        powerplay_wickets=int(row["powerplay_wickets"]),
        death_runs=int(row["death_runs"]),
        death_balls=int(row["death_balls"]),
        death_wickets=int(row["death_wickets"]),
        team_wins=int(row["team_wins"]),
        team_matches=int(row["team_matches"]),
        win_percentage=float(row["win_percentage"]) if row["win_percentage"] is not None else None,
        raw_performance_composite=float(row["raw_performance_composite"]),
        match_ids=_loads_list(row["match_ids_json"]),
        raw_stats=_loads_dict(row["raw_stats_json"]),
        formula_version=row["formula_version"],
        created_at_utc=row["created_at_utc"],
    )


def _parse_apdi_row(row: Any) -> APDIRecordResponse:
    def _loads_list(raw: Any) -> List[Any]:
        try:
            val = json.loads(raw) if raw else []
            return val if isinstance(val, list) else []
        except Exception:
            return []

    def _loads_dict(raw: Any) -> Dict[str, Any]:
        try:
            val = json.loads(raw) if raw else {}
            return val if isinstance(val, dict) else {}
        except Exception:
            return {}

    return APDIRecordResponse(
        record_id=row["record_id"],
        run_id=row["run_id"],
        entity_id=row["entity_id"],
        entity_name=row["entity_name"],
        entity_type=row["entity_type"],
        role_cohort=row["role_cohort"],
        tournament=row["tournament"],
        comparison_window=row["comparison_window"],
        raw_attention_score=float(row["raw_attention_score"]),
        normalized_attention_score=(
            float(row["normalized_attention_score"])
            if row["normalized_attention_score"] is not None
            else None
        ),
        raw_performance_score=float(row["raw_performance_score"]),
        normalized_performance_score=(
            float(row["normalized_performance_score"])
            if row["normalized_performance_score"] is not None
            else None
        ),
        apdi_value=float(row["apdi_value"]) if row["apdi_value"] is not None else None,
        discrepancy_category=row["discrepancy_category"],
        evidence_sufficiency_status=row["evidence_sufficiency_status"],
        sample_size_indicators=_loads_dict(row["sample_size_indicators_json"]),
        data_quality_warnings=_loads_list(row["data_quality_warnings_json"]),
        framing_breakdown=_loads_dict(row["framing_breakdown_json"]),
        evidence_lineage=_loads_dict(row["evidence_lineage_json"]),
        formula_version=row["formula_version"],
        created_at_utc=row["created_at_utc"],
    )


def _resolve_entity_alias_ids(storage: SQLiteStorageManager, entity_id: str) -> List[str]:
    """Resolves potential alias IDs for an entity across players, teams, and gazetteer slugs."""
    ids = [entity_id]
    with storage._get_connection() as conn:
        clean_key = entity_id.replace("player_", "").replace("_", " ").strip()
        p_row = conn.execute(
            "SELECT player_id, full_name FROM players WHERE player_id = ? OR full_name LIKE ?;",
            (entity_id, f"%{clean_key}%"),
        ).fetchone()
        if p_row:
            p_id = p_row["player_id"]
            if p_id not in ids:
                ids.append(p_id)
            full_name = p_row["full_name"] or ""
            import re
            clean = re.sub(r"[^a-z0-9]+", "_", full_name.lower()).strip("_")
            if clean:
                gaz_slug = f"player_{clean}"
                if gaz_slug not in ids:
                    ids.append(gaz_slug)
        t_row = conn.execute(
            "SELECT team_id, name FROM teams WHERE team_id = ? OR name LIKE ?;",
            (entity_id, f"%{entity_id}%"),
        ).fetchone()
        if t_row:
            t_id = t_row["team_id"]
            if t_id not in ids:
                ids.append(t_id)
    return ids


@router.get("/overview", response_model=AnalyticsOverviewResponse)
def get_analytics_overview(
    tournament: Optional[str] = Query(None, description="Tournament filter"),
    storage: SQLiteStorageManager = Depends(get_storage),
    preflight: AnalyticsPreflight = Depends(get_preflight),
) -> AnalyticsOverviewResponse:
    """Provides high-level summary of analytical runs, APDI distributions, and preflight status."""
    summary = storage.get_analytics_summary(tournament)
    preflight_result = preflight.run_preflight(tournament)

    sufficiency = (
        preflight_result.status.value
        if hasattr(preflight_result.status, "value")
        else str(preflight_result.status)
    )

    return AnalyticsOverviewResponse(
        tournament=summary["tournament"],
        attention_metrics_count=summary["attention_metrics_count"],
        performance_metrics_count=summary["performance_metrics_count"],
        apdi_records_count=summary["apdi_records_count"],
        over_attended_count=summary["over_attended_count"],
        under_attended_count=summary["under_attended_count"],
        balanced_count=summary["balanced_count"],
        insufficient_data_count=summary["insufficient_data_count"],
        analytics_runs_count=summary["analytics_runs_count"],
        preflight_status=sufficiency,
        is_eligible=preflight_result.is_eligible,
        warnings=preflight_result.warnings,
    )


@router.get("/attention", response_model=PaginatedResponse[MediaAttentionResponse])
def list_attention_metrics(
    tournament: Optional[str] = Query(None, description="Tournament filter"),
    entity_id: Optional[str] = Query(None, description="Filter by player or team identifier"),
    pagination: Tuple[int, int] = Depends(pagination_params),
    storage: SQLiteStorageManager = Depends(get_storage),
) -> PaginatedResponse[MediaAttentionResponse]:
    """Retrieves paginated media attention metrics and prominence scores."""
    limit, offset = pagination
    where_clauses: List[str] = []
    params: List[Any] = []

    if tournament:
        where_clauses.append("tournament = ?")
        params.append(tournament)
    if entity_id:
        cand_ids = _resolve_entity_alias_ids(storage, entity_id)
        placeholders = ", ".join("?" for _ in cand_ids)
        where_clauses.append(f"entity_id IN ({placeholders})")
        params.extend(cand_ids)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    with storage._get_connection() as conn:
        count_query = f"SELECT COUNT(*) FROM attention_metrics {where_sql};"
        total = conn.execute(count_query, params).fetchone()[0]

        query = f"""
            SELECT * FROM attention_metrics
            {where_sql}
            ORDER BY raw_attention_composite DESC, metric_id ASC
            LIMIT ? OFFSET ?;
        """
        rows = conn.execute(query, params + [limit, offset]).fetchall()
        items = [_parse_attention_row(r) for r in rows]

    return PaginatedResponse.create(items=items, total=total, limit=limit, offset=offset)


@router.get("/performance", response_model=PaginatedResponse[CricketPerformanceResponse])
def list_performance_metrics(
    tournament: Optional[str] = Query(None, description="Tournament filter"),
    entity_id: Optional[str] = Query(None, description="Filter by player or team identifier"),
    role: Optional[str] = Query(None, description="Filter by role (batter/bowler/all_rounder/team)"),
    pagination: Tuple[int, int] = Depends(pagination_params),
    storage: SQLiteStorageManager = Depends(get_storage),
) -> PaginatedResponse[CricketPerformanceResponse]:
    """Retrieves objective match performance metrics calculated strictly from deliveries."""
    limit, offset = pagination
    where_clauses: List[str] = []
    params: List[Any] = []

    if tournament:
        where_clauses.append("tournament = ?")
        params.append(tournament)
    if entity_id:
        where_clauses.append("entity_id = ?")
        params.append(entity_id)
    if role:
        where_clauses.append("role = ?")
        params.append(role.lower())

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    with storage._get_connection() as conn:
        count_query = f"SELECT COUNT(*) FROM performance_metrics {where_sql};"
        total = conn.execute(count_query, params).fetchone()[0]

        query = f"""
            SELECT * FROM performance_metrics
            {where_sql}
            ORDER BY raw_performance_composite DESC, metric_id ASC
            LIMIT ? OFFSET ?;
        """
        rows = conn.execute(query, params + [limit, offset]).fetchall()
        items = [_parse_performance_row(r) for r in rows]

    return PaginatedResponse.create(items=items, total=total, limit=limit, offset=offset)


@router.get("/framing", response_model=NarrativeFramingResponse)
def get_entity_framing(
    entity_id: str = Query(..., description="Target player or team identifier"),
    storage: SQLiteStorageManager = Depends(get_storage),
    framing_calc: NarrativeFramingCalculator = Depends(get_framing_calculator),
) -> NarrativeFramingResponse:
    """Calculates sentiment framing and publisher variance for a specific player or team."""
    cand_ids = _resolve_entity_alias_ids(storage, entity_id)
    placeholders = ", ".join("?" for _ in cand_ids)

    with storage._get_connection() as conn:
        # Check direct mentions or sentiment baseline bindings
        sent_rows = conn.execute(
            f"""
            SELECT * FROM sentiment_baselines
            WHERE target_entity_id IN ({placeholders});
            """,
            cand_ids,
        ).fetchall()

        sentiments = [dict(r) for r in sent_rows]

        # Fetch supporting paragraphs and article metadata
        para_rows = conn.execute("SELECT paragraph_id, article_id, text FROM article_paragraphs;").fetchall()
        paragraphs_map = {r["paragraph_id"]: dict(r) for r in para_rows}

        art_rows = conn.execute("SELECT article_id, source_domain FROM articles;").fetchall()
        articles_map = {r["article_id"]: dict(r) for r in art_rows}

    framing_metrics = framing_calc.compute_framing(
        entity_id=entity_id,
        sentiments=sentiments,
        paragraphs=paragraphs_map,
        articles=articles_map,
    )

    return NarrativeFramingResponse(
        entity_id=framing_metrics.entity_id,
        positive_count=framing_metrics.positive_count,
        neutral_count=framing_metrics.neutral_count,
        negative_count=framing_metrics.negative_count,
        total_framed_passages=framing_metrics.total_framed_passages,
        net_framing_score=framing_metrics.net_framing_score,
        source_framing_breakdown=framing_metrics.source_framing_breakdown,
        topic_distribution=framing_metrics.topic_distribution,
        supporting_samples=framing_metrics.supporting_samples,
    )


@router.get("/apdi", response_model=PaginatedResponse[APDIRecordResponse])
def list_apdi_records(
    tournament: Optional[str] = Query(None, description="Tournament filter"),
    role_cohort: Optional[str] = Query(None, description="Role cohort filter (batter/bowler/team)"),
    discrepancy_category: Optional[str] = Query(
        None, description="OVER_ATTENDED / UNDER_ATTENDED / BALANCED / INSUFFICIENT_DATA"
    ),
    pagination: Tuple[int, int] = Depends(pagination_params),
    storage: SQLiteStorageManager = Depends(get_storage),
) -> PaginatedResponse[APDIRecordResponse]:
    """Retrieves Attention-to-Performance Discrepancy Index (APDI) records."""
    limit, offset = pagination
    where_clauses: List[str] = []
    params: List[Any] = []

    if tournament:
        where_clauses.append("tournament = ?")
        params.append(tournament)
    if role_cohort:
        where_clauses.append("role_cohort = ?")
        params.append(role_cohort.lower())
    if discrepancy_category:
        where_clauses.append("discrepancy_category = ?")
        params.append(discrepancy_category.upper())

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    with storage._get_connection() as conn:
        count_query = f"SELECT COUNT(*) FROM apdi_records {where_sql};"
        total = conn.execute(count_query, params).fetchone()[0]

        query = f"""
            SELECT * FROM apdi_records
            {where_sql}
            ORDER BY apdi_value DESC NULLS LAST, record_id ASC
            LIMIT ? OFFSET ?;
        """
        rows = conn.execute(query, params + [limit, offset]).fetchall()
        items = [_parse_apdi_row(r) for r in rows]

    return PaginatedResponse.create(items=items, total=total, limit=limit, offset=offset)


@router.get("/apdi/{entity_id}", response_model=APDIRecordResponse)
def get_entity_apdi(
    entity_id: str,
    storage: SQLiteStorageManager = Depends(get_storage),
) -> APDIRecordResponse:
    """Retrieves the latest APDI record for a specific entity or returns 404."""
    cand_ids = _resolve_entity_alias_ids(storage, entity_id)
    placeholders = ", ".join("?" for _ in cand_ids)

    with storage._get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT * FROM apdi_records
            WHERE entity_id IN ({placeholders})
            ORDER BY created_at_utc DESC
            LIMIT 1;
            """,
            cand_ids,
        ).fetchone()

        if not row:
            raise ResourceNotFoundError("apdi", entity_id)

        return _parse_apdi_row(row)


@router.get("/validation", response_model=AnalyticsValidationResponse)
def validate_analytics(
    storage: SQLiteStorageManager = Depends(get_storage),
) -> AnalyticsValidationResponse:
    """Validates structural and mathematical invariants across Phase 6A analytics tables."""
    issues: List[str] = []

    with storage._get_connection() as conn:
        # Invariant 1: APDI records with INSUFFICIENT_DATA must have null apdi_value
        invalid_apdi = conn.execute(
            """
            SELECT COUNT(*) FROM apdi_records
            WHERE discrepancy_category = 'INSUFFICIENT_DATA' AND apdi_value IS NOT NULL;
            """
        ).fetchone()[0]
        if invalid_apdi > 0:
            issues.append(f"Found {invalid_apdi} INSUFFICIENT_DATA records with non-null apdi_value")

        # Invariant 2: Normalized attention should be between 0 and 1
        invalid_att = conn.execute(
            """
            SELECT COUNT(*) FROM apdi_records
            WHERE normalized_attention_score IS NOT NULL
              AND (normalized_attention_score < 0.0 OR normalized_attention_score > 1.0);
            """
        ).fetchone()[0]
        if invalid_att > 0:
            issues.append(f"Found {invalid_att} APDI records with out-of-bounds normalized attention")

        # Invariant 3: Normalized performance should be between 0 and 1
        invalid_perf = conn.execute(
            """
            SELECT COUNT(*) FROM apdi_records
            WHERE normalized_performance_score IS NOT NULL
              AND (normalized_performance_score < 0.0 OR normalized_performance_score > 1.0);
            """
        ).fetchone()[0]
        if invalid_perf > 0:
            issues.append(f"Found {invalid_perf} APDI records with out-of-bounds normalized performance")

    return AnalyticsValidationResponse(
        is_valid=len(issues) == 0,
        issues=issues,
    )
