"""API Routes for Canonical Player Entities."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple
from fastapi import APIRouter, Depends, Query

from src.api.dependencies import get_storage, pagination_params
from src.api.errors import ResourceNotFoundError
from src.api.schemas.common import PaginatedResponse
from src.api.schemas.entities import PlayerResponse
from src.storage.sqlite_manager import SQLiteStorageManager

router = APIRouter(prefix="/players", tags=["Players & Teams"])


def _parse_player_row(row: Any) -> PlayerResponse:
    aliases_raw = row["aliases_json"]
    try:
        aliases = json.loads(aliases_raw) if aliases_raw else []
    except Exception:
        aliases = []

    return PlayerResponse(
        player_id=row["player_id"],
        full_name=row["full_name"],
        cricsheet_id=row["cricsheet_id"],
        primary_team_id=row["primary_team_id"],
        batting_style=row["batting_style"],
        bowling_style=row["bowling_style"],
        aliases=aliases if isinstance(aliases, list) else [],
    )


@router.get("", response_model=PaginatedResponse[PlayerResponse])
def list_players(
    team_id: Optional[str] = Query(None, description="Filter by primary team identifier"),
    search: Optional[str] = Query(None, description="Search by full name or alias substring"),
    pagination: Tuple[int, int] = Depends(pagination_params),
    storage: SQLiteStorageManager = Depends(get_storage),
) -> PaginatedResponse[PlayerResponse]:
    """Retrieves paginated canonical players with safe filtering and alias resolution."""
    limit, offset = pagination
    where_clauses: List[str] = []
    params: List[Any] = []

    if team_id:
        where_clauses.append("primary_team_id = ?")
        params.append(team_id)
    if search:
        search_pattern = f"%{search.strip()}%"
        where_clauses.append("(full_name LIKE ? OR aliases_json LIKE ?)")
        params.extend([search_pattern, search_pattern])

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    with storage._get_connection() as conn:
        count_query = f"SELECT COUNT(*) FROM players {where_sql};"
        total = conn.execute(count_query, params).fetchone()[0]

        query = f"""
            SELECT * FROM players
            {where_sql}
            ORDER BY full_name ASC, player_id ASC
            LIMIT ? OFFSET ?;
        """
        rows = conn.execute(query, params + [limit, offset]).fetchall()
        items = [_parse_player_row(r) for r in rows]

    return PaginatedResponse.create(items=items, total=total, limit=limit, offset=offset)


@router.get("/{player_id}", response_model=PlayerResponse)
def get_player(
    player_id: str,
    storage: SQLiteStorageManager = Depends(get_storage),
) -> PlayerResponse:
    """Retrieves a single canonical player by identifier or returns 404."""
    with storage._get_connection() as conn:
        row = conn.execute("SELECT * FROM players WHERE player_id = ?;", (player_id,)).fetchone()
        if not row:
            raise ResourceNotFoundError("players", player_id)
        return _parse_player_row(row)
