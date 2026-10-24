"""API Routes for Canonical Team Entities."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple
from fastapi import APIRouter, Depends, Query

from src.api.dependencies import get_storage, pagination_params
from src.api.errors import ResourceNotFoundError
from src.api.schemas.common import PaginatedResponse
from src.api.schemas.entities import TeamResponse
from src.storage.sqlite_manager import SQLiteStorageManager

router = APIRouter(prefix="/teams", tags=["Players & Teams"])


def _parse_team_row(row: Any) -> TeamResponse:
    aliases_raw = row["aliases_json"]
    try:
        aliases = json.loads(aliases_raw) if aliases_raw else []
    except Exception:
        aliases = []

    return TeamResponse(
        team_id=row["team_id"],
        name=row["name"],
        aliases=aliases if isinstance(aliases, list) else [],
    )


@router.get("", response_model=PaginatedResponse[TeamResponse])
def list_teams(
    search: Optional[str] = Query(None, description="Search by team name or alias substring"),
    pagination: Tuple[int, int] = Depends(pagination_params),
    storage: SQLiteStorageManager = Depends(get_storage),
) -> PaginatedResponse[TeamResponse]:
    """Retrieves paginated canonical teams with safe name/alias search."""
    limit, offset = pagination
    where_clauses: List[str] = []
    params: List[Any] = []

    if search:
        search_pattern = f"%{search.strip()}%"
        where_clauses.append("(name LIKE ? OR aliases_json LIKE ?)")
        params.extend([search_pattern, search_pattern])

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    with storage._get_connection() as conn:
        count_query = f"SELECT COUNT(*) FROM teams {where_sql};"
        total = conn.execute(count_query, params).fetchone()[0]

        query = f"""
            SELECT * FROM teams
            {where_sql}
            ORDER BY name ASC, team_id ASC
            LIMIT ? OFFSET ?;
        """
        rows = conn.execute(query, params + [limit, offset]).fetchall()
        items = [_parse_team_row(r) for r in rows]

    return PaginatedResponse.create(items=items, total=total, limit=limit, offset=offset)


@router.get("/{team_id}", response_model=TeamResponse)
def get_team(
    team_id: str,
    storage: SQLiteStorageManager = Depends(get_storage),
) -> TeamResponse:
    """Retrieves a single canonical team by identifier or returns 404."""
    with storage._get_connection() as conn:
        row = conn.execute("SELECT * FROM teams WHERE team_id = ?;", (team_id,)).fetchone()
        if not row:
            raise ResourceNotFoundError("teams", team_id)
        return _parse_team_row(row)
