"""API Routes for Ball-by-Ball Commentary."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple
from fastapi import APIRouter, Depends, Query

from src.api.dependencies import get_storage, pagination_params
from src.api.errors import ResourceNotFoundError
from src.api.schemas.common import PaginatedResponse
from src.api.schemas.editorial import CommentaryResponse
from src.storage.sqlite_manager import SQLiteStorageManager

router = APIRouter(prefix="/commentary", tags=["Articles & Editorial Commentary"])


def _parse_commentary(row: Any) -> CommentaryResponse:
    tags_raw = row["event_tags_json"]
    try:
        tags = json.loads(tags_raw) if tags_raw else []
    except Exception:
        tags = []

    return CommentaryResponse(
        commentary_id=row["commentary_id"],
        match_id=row["match_id"],
        innings=int(row["innings"]),
        over_num=int(row["over_num"]),
        ball_num=int(row["ball_num"]),
        bowler_raw=row["bowler_raw"],
        batter_raw=row["batter_raw"],
        text=row["text"],
        event_tags=tags if isinstance(tags, list) else [],
        source_domain=row["source_domain"],
        harvest_timestamp_utc=row["harvest_timestamp_utc"],
        provenance_id=row["provenance_id"],
    )


@router.get("", response_model=PaginatedResponse[CommentaryResponse])
def list_commentary(
    match_id: Optional[str] = Query(None, description="Filter by match identifier"),
    innings: Optional[int] = Query(None, ge=1, le=4, description="Filter by innings"),
    over_num: Optional[int] = Query(None, ge=0, le=50, description="Filter by over number"),
    source_domain: Optional[str] = Query(None, description="Filter by source domain"),
    pagination: Tuple[int, int] = Depends(pagination_params),
    storage: SQLiteStorageManager = Depends(get_storage),
) -> PaginatedResponse[CommentaryResponse]:
    """Retrieves paginated ball-by-ball commentary entries."""
    limit, offset = pagination
    where_clauses: List[str] = []
    params: List[Any] = []

    if match_id:
        where_clauses.append("match_id = ?")
        params.append(match_id)
    if innings is not None:
        where_clauses.append("innings = ?")
        params.append(innings)
    if over_num is not None:
        where_clauses.append("over_num = ?")
        params.append(over_num)
    if source_domain:
        where_clauses.append("source_domain = ?")
        params.append(source_domain.strip().lower())

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    with storage._get_connection() as conn:
        count_query = f"SELECT COUNT(*) FROM commentary_entries {where_sql};"
        total = conn.execute(count_query, params).fetchone()[0]

        query = f"""
            SELECT * FROM commentary_entries
            {where_sql}
            ORDER BY innings ASC, over_num ASC, ball_num ASC, commentary_id ASC
            LIMIT ? OFFSET ?;
        """
        rows = conn.execute(query, params + [limit, offset]).fetchall()
        items = [_parse_commentary(r) for r in rows]

    return PaginatedResponse.create(items=items, total=total, limit=limit, offset=offset)


@router.get("/{commentary_id}", response_model=CommentaryResponse)
def get_commentary(
    commentary_id: str,
    storage: SQLiteStorageManager = Depends(get_storage),
) -> CommentaryResponse:
    """Retrieves a single commentary entry by identifier or returns 404."""
    with storage._get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM commentary_entries WHERE commentary_id = ?;", (commentary_id,)
        ).fetchone()
        if not row:
            raise ResourceNotFoundError("commentary", commentary_id)
        return _parse_commentary(row)
