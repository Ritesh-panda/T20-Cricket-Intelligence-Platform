"""API Routes for Matches, Deliveries, and Match Performance Scorecards."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple
from fastapi import APIRouter, Depends, Query

from src.api.dependencies import get_storage, pagination_params
from src.api.errors import ResourceNotFoundError
from src.api.schemas.common import PaginatedResponse
from src.api.schemas.matches import (
    DeliveryResponse,
    MatchBatterScore,
    MatchBowlerScore,
    MatchPerformanceScorecard,
    MatchResponse,
    MatchTeamScore,
)
from src.storage.sqlite_manager import SQLiteStorageManager

router = APIRouter(prefix="/matches", tags=["Matches & Cricket Performance"])


def _parse_match_row(row: Any) -> MatchResponse:
    metadata_raw = row["metadata_json"]
    try:
        metadata = json.loads(metadata_raw) if metadata_raw else {}
    except Exception:
        metadata = {}

    return MatchResponse(
        match_id=row["match_id"],
        tournament=row["tournament"],
        season=row["season"],
        match_date=row["match_date"],
        venue=row["venue"],
        city=row["city"],
        team1_id=row["team1_id"],
        team2_id=row["team2_id"],
        toss_winner_id=row["toss_winner_id"],
        toss_decision=row["toss_decision"],
        winner_id=row["winner_id"],
        win_by_runs=row["win_by_runs"],
        win_by_wickets=row["win_by_wickets"],
        player_of_match_id=row["player_of_match_id"],
        target_runs=row["target_runs"],
        metadata=metadata,
        provenance_id=row["provenance_id"],
    )


def _parse_delivery_row(row: Any) -> DeliveryResponse:
    return DeliveryResponse(
        delivery_id=row["delivery_id"],
        match_id=row["match_id"],
        innings=int(row["innings"]),
        over_num=int(row["over_num"]),
        ball_num=int(row["ball_num"]),
        batter_id=row["batter_id"],
        bowler_id=row["bowler_id"],
        non_striker_id=row["non_striker_id"],
        batter_runs=int(row["batter_runs"]),
        extra_runs=int(row["extra_runs"]),
        extra_type=row["extra_type"],
        total_runs=int(row["total_runs"]),
        is_legal=bool(row["is_legal"]),
        is_wicket=bool(row["is_wicket"]),
        wicket_kind=row["wicket_kind"],
        player_dismissed_id=row["player_dismissed_id"],
        phase=row["phase"],
    )


@router.get("", response_model=PaginatedResponse[MatchResponse])
def list_matches(
    tournament: Optional[str] = Query(None, description="Filter by tournament name"),
    season: Optional[str] = Query(None, description="Filter by season"),
    team_id: Optional[str] = Query(None, description="Filter by participating team ID"),
    pagination: Tuple[int, int] = Depends(pagination_params),
    storage: SQLiteStorageManager = Depends(get_storage),
) -> PaginatedResponse[MatchResponse]:
    """Retrieves paginated match metadata records with safe parameterized filtering."""
    limit, offset = pagination
    where_clauses: List[str] = []
    params: List[Any] = []

    if tournament:
        where_clauses.append("tournament = ?")
        params.append(tournament)
    if season:
        where_clauses.append("season = ?")
        params.append(season)
    if team_id:
        where_clauses.append("(team1_id = ? OR team2_id = ?)")
        params.extend([team_id, team_id])

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    with storage._get_connection() as conn:
        count_query = f"SELECT COUNT(*) FROM matches {where_sql};"
        total = conn.execute(count_query, params).fetchone()[0]

        query = f"""
            SELECT * FROM matches
            {where_sql}
            ORDER BY match_date DESC, match_id ASC
            LIMIT ? OFFSET ?;
        """
        rows = conn.execute(query, params + [limit, offset]).fetchall()
        items = [_parse_match_row(r) for r in rows]

    return PaginatedResponse.create(items=items, total=total, limit=limit, offset=offset)


@router.get("/{match_id}", response_model=MatchResponse)
def get_match(
    match_id: str,
    storage: SQLiteStorageManager = Depends(get_storage),
) -> MatchResponse:
    """Retrieves single match record by identifier or returns 404."""
    with storage._get_connection() as conn:
        row = conn.execute("SELECT * FROM matches WHERE match_id = ?;", (match_id,)).fetchone()
        if not row:
            raise ResourceNotFoundError("matches", match_id)
        return _parse_match_row(row)


@router.get("/{match_id}/deliveries", response_model=PaginatedResponse[DeliveryResponse])
def get_match_deliveries(
    match_id: str,
    innings: Optional[int] = Query(None, ge=1, le=4, description="Filter by innings number"),
    over_num: Optional[int] = Query(None, ge=0, le=50, description="Filter by over number"),
    phase: Optional[str] = Query(None, description="Filter by match phase (powerplay/middle/death)"),
    pagination: Tuple[int, int] = Depends(pagination_params),
    storage: SQLiteStorageManager = Depends(get_storage),
) -> PaginatedResponse[DeliveryResponse]:
    """Retrieves structured delivery fact rows for a given match."""
    limit, offset = pagination

    with storage._get_connection() as conn:
        # Verify match existence first
        match_exists = conn.execute(
            "SELECT 1 FROM matches WHERE match_id = ?;", (match_id,)
        ).fetchone()
        if not match_exists:
            raise ResourceNotFoundError("matches", match_id)

        where_clauses = ["match_id = ?"]
        params: List[Any] = [match_id]

        if innings is not None:
            where_clauses.append("innings = ?")
            params.append(innings)
        if over_num is not None:
            where_clauses.append("over_num = ?")
            params.append(over_num)
        if phase:
            where_clauses.append("phase = ?")
            params.append(phase)

        where_sql = f"WHERE {' AND '.join(where_clauses)}"

        count_query = f"SELECT COUNT(*) FROM deliveries {where_sql};"
        total = conn.execute(count_query, params).fetchone()[0]

        query = f"""
            SELECT * FROM deliveries
            {where_sql}
            ORDER BY innings ASC, over_num ASC, ball_num ASC, delivery_id ASC
            LIMIT ? OFFSET ?;
        """
        rows = conn.execute(query, params + [limit, offset]).fetchall()
        items = [_parse_delivery_row(r) for r in rows]

    return PaginatedResponse.create(items=items, total=total, limit=limit, offset=offset)


@router.get("/{match_id}/performance", response_model=MatchPerformanceScorecard)
def get_match_performance(
    match_id: str,
    storage: SQLiteStorageManager = Depends(get_storage),
) -> MatchPerformanceScorecard:
    """Calculates or retrieves aggregated player and team performance for a match."""
    with storage._get_connection() as conn:
        match_row = conn.execute("SELECT * FROM matches WHERE match_id = ?;", (match_id,)).fetchone()
        if not match_row:
            raise ResourceNotFoundError("matches", match_id)

        deliveries = conn.execute(
            """
            SELECT * FROM deliveries
            WHERE match_id = ?
            ORDER BY innings ASC, over_num ASC, ball_num ASC;
            """,
            (match_id,),
        ).fetchall()

    # Aggregate performance from deliveries
    batters_dict: Dict[str, Dict[str, Any]] = {}
    bowlers_dict: Dict[str, Dict[str, Any]] = {}
    teams_dict: Dict[int, Dict[str, Any]] = {}

    team1_id = match_row["team1_id"]
    team2_id = match_row["team2_id"]

    for d in deliveries:
        innings = int(d["innings"])
        batter_id = d["batter_id"]
        bowler_id = d["bowler_id"]
        batter_runs = int(d["batter_runs"])
        extra_runs = int(d["extra_runs"])
        total_runs = int(d["total_runs"])
        extra_type = d["extra_type"]
        is_legal = bool(d["is_legal"])
        is_wicket = bool(d["is_wicket"])
        wicket_kind = d["wicket_kind"]
        player_dismissed_id = d["player_dismissed_id"]

        # Team innings aggregation
        if innings not in teams_dict:
            # Innings 1 is team1 or toss winner batting first; best effort mapping
            team_assigned = team1_id if innings == 1 else team2_id
            teams_dict[innings] = {
                "team_id": team_assigned,
                "innings": innings,
                "total_runs": 0,
                "total_wickets": 0,
                "legal_balls": 0,
            }
        teams_dict[innings]["total_runs"] += total_runs
        if is_wicket:
            teams_dict[innings]["total_wickets"] += 1
        if is_legal:
            teams_dict[innings]["legal_balls"] += 1

        # Batter aggregation
        if batter_id not in batters_dict:
            batters_dict[batter_id] = {
                "player_id": batter_id,
                "runs": 0,
                "balls": 0,
                "fours": 0,
                "sixes": 0,
                "is_out": False,
                "dismissal_kind": None,
            }
        batters_dict[batter_id]["runs"] += batter_runs
        # Legal delivery faced or no-ball counts as ball faced (wides do not)
        if extra_type != "wides":
            batters_dict[batter_id]["balls"] += 1
        if batter_runs == 4:
            batters_dict[batter_id]["fours"] += 1
        elif batter_runs == 6:
            batters_dict[batter_id]["sixes"] += 1

        # Check dismissal
        if is_wicket and player_dismissed_id:
            if player_dismissed_id in batters_dict:
                batters_dict[player_dismissed_id]["is_out"] = True
                batters_dict[player_dismissed_id]["dismissal_kind"] = wicket_kind
            else:
                batters_dict[player_dismissed_id] = {
                    "player_id": player_dismissed_id,
                    "runs": 0,
                    "balls": 0,
                    "fours": 0,
                    "sixes": 0,
                    "is_out": True,
                    "dismissal_kind": wicket_kind,
                }

        # Bowler aggregation
        if bowler_id not in bowlers_dict:
            bowlers_dict[bowler_id] = {
                "player_id": bowler_id,
                "legal_balls": 0,
                "runs_conceded": 0,
                "wickets": 0,
            }
        if is_legal:
            bowlers_dict[bowler_id]["legal_balls"] += 1
        # Runs charged to bowler include batter runs plus wides and noballs
        if extra_type in ("wides", "noballs") or extra_type is None:
            bowlers_dict[bowler_id]["runs_conceded"] += total_runs
        else:
            bowlers_dict[bowler_id]["runs_conceded"] += batter_runs

        if is_wicket and wicket_kind not in ("run out", "retired hurt"):
            bowlers_dict[bowler_id]["wickets"] += 1

    # Format batter scores
    batters: List[MatchBatterScore] = []
    for b in batters_dict.values():
        sr = round((b["runs"] / b["balls"]) * 100.0, 2) if b["balls"] > 0 else 0.0
        batters.append(
            MatchBatterScore(
                player_id=b["player_id"],
                runs=b["runs"],
                balls=b["balls"],
                fours=b["fours"],
                sixes=b["sixes"],
                strike_rate=sr,
                is_out=b["is_out"],
                dismissal_kind=b["dismissal_kind"],
            )
        )

    # Format bowler scores
    bowlers: List[MatchBowlerScore] = []
    for bw in bowlers_dict.values():
        overs = (bw["legal_balls"] // 6) + ((bw["legal_balls"] % 6) / 10.0)
        economy = (
            round(bw["runs_conceded"] / (bw["legal_balls"] / 6.0), 2)
            if bw["legal_balls"] > 0
            else 0.0
        )
        bowlers.append(
            MatchBowlerScore(
                player_id=bw["player_id"],
                overs=overs,
                legal_balls=bw["legal_balls"],
                runs_conceded=bw["runs_conceded"],
                wickets=bw["wickets"],
                economy=economy,
            )
        )

    # Format team scores
    team_scores: List[MatchTeamScore] = []
    for t in sorted(teams_dict.values(), key=lambda x: x["innings"]):
        overs = (t["legal_balls"] // 6) + ((t["legal_balls"] % 6) / 10.0)
        team_scores.append(
            MatchTeamScore(
                team_id=t["team_id"],
                innings=t["innings"],
                total_runs=t["total_runs"],
                total_wickets=t["total_wickets"],
                legal_overs=overs,
            )
        )

    return MatchPerformanceScorecard(
        match_id=match_row["match_id"],
        tournament=match_row["tournament"],
        match_date=match_row["match_date"],
        venue=match_row["venue"],
        winner_id=match_row["winner_id"],
        team_scores=team_scores,
        batters=batters,
        bowlers=bowlers,
    )
