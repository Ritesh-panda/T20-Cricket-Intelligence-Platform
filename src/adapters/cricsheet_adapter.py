"""Cricsheet Ingestion Adapter for T20 Cricket Intelligence Platform.

Ingests and validates official Cricsheet match JSON data (v1.0.0 - v1.2.0),
maps player registry IDs to canonical entities, and reconciles scorecard facts.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from src.adapters.base import BaseSourceAdapter
from src.models.canonical import (
    DeliveryRecord,
    MatchPhase,
    MatchRecord,
    PlayerRecord,
    SourceRecord,
    TeamRecord,
)

logger = logging.getLogger(__name__)

NON_BOWLER_WICKETS = {
    "run out",
    "retired hurt",
    "retired out",
    "obstructing the field",
    "timed out",
    "handled the ball",
}


@dataclass
class ScoreReconciliationReport:
    """Detailed score reconciliation results across match innings."""
    match_id: str
    innings_totals: Dict[int, int] = field(default_factory=dict)
    innings_wickets: Dict[int, int] = field(default_factory=dict)
    target_runs: Optional[int] = None
    winner_reconciled: bool = True
    reconciliation_notes: List[str] = field(default_factory=list)


@dataclass
class CricsheetParseResult:
    """Container for parsed canonical entities from a Cricsheet file."""
    match: MatchRecord
    teams: List[TeamRecord]
    players: List[PlayerRecord]
    deliveries: List[DeliveryRecord]
    provenance: SourceRecord
    reconciliation: ScoreReconciliationReport
    warnings: List[str] = field(default_factory=list)


class CricsheetAdapter(BaseSourceAdapter):
    """Parses, validates, and normalizes Cricsheet match JSON datasets."""

    def __init__(self):
        super().__init__(
            source_name="cricsheet",
            rate_limit_rps=0.0,  # Local file ingestion
            user_agent="T20CricketResearchBot/1.0 (local Cricsheet parser)",
        )

    def _determine_phase(self, over_number: int, innings: int) -> MatchPhase:
        """Determines match phase for standard 20-over T20 matches."""
        if innings > 2:
            return MatchPhase.SUPER_OVER
        if over_number < 6:
            return MatchPhase.POWERPLAY
        elif over_number < 15:
            return MatchPhase.MIDDLE
        else:
            return MatchPhase.DEATH

    def parse_file(self, file_path: str | Path) -> CricsheetParseResult:
        """Loads and parses a single Cricsheet JSON file from disk."""
        path = Path(file_path)
        with open(path, "rb") as f:
            raw_bytes = f.read()
        match_id_hint = path.stem
        return self.parse_json_bytes(raw_bytes, source_identifier=path.name, match_id_hint=match_id_hint)

    def parse_json_bytes(
        self,
        raw_bytes: bytes,
        source_identifier: str = "cricsheet_match.json",
        match_id_hint: Optional[str] = None,
    ) -> CricsheetParseResult:
        """Parses raw Cricsheet JSON bytes into canonical models."""
        raw_data = json.loads(raw_bytes.decode("utf-8"))
        warnings: List[str] = []

        # 1. Provenance
        prov = self.create_provenance_record(
            source_identifier=source_identifier,
            raw_bytes=raw_bytes,
            source_url="https://cricsheet.org/downloads/t20s_json.zip",
            license_tag="ODbL-1.0",
            redistributable=True,
        )

        info = raw_data.get("info", {})
        if not info:
            raise ValueError("Malformed Cricsheet JSON: 'info' section missing")

        # 2. Match Identification
        dates = info.get("dates", [])
        match_date = dates[0] if dates else "1970-01-01"
        teams_raw = info.get("teams", [])
        if len(teams_raw) < 2:
            raise ValueError("Malformed Cricsheet JSON: 'teams' must contain at least 2 teams")

        team1_name, team2_name = teams_raw[0], teams_raw[1]
        team1_id = team1_name[:3].upper().replace(" ", "")
        team2_id = team2_name[:3].upper().replace(" ", "")

        # Stable match ID
        if match_id_hint:
            match_id = f"cric_{match_id_hint}"
        else:
            date_clean = match_date.replace("-", "")
            match_id = f"cric_{date_clean}_{team1_id.lower()}_{team2_id.lower()}"

        # 3. Teams
        team1_record = TeamRecord(team_id=team1_id, name=team1_name, aliases=[team1_name])
        team2_record = TeamRecord(team_id=team2_id, name=team2_name, aliases=[team2_name])
        teams_list = [team1_record, team2_record]

        # 4. Player Registry
        registry_people = info.get("registry", {}).get("people", {})
        players_by_team = info.get("players", {})
        players_dict: Dict[str, PlayerRecord] = {}

        for team_name, player_names in players_by_team.items():
            t_id = team1_id if team_name == team1_name else team2_id
            for p_name in player_names:
                cric_id = registry_people.get(p_name)
                clean_slug = p_name.lower().replace(" ", "_").replace(".", "").strip()
                canonical_p_id = f"player_{clean_slug}"
                if canonical_p_id not in players_dict:
                    players_dict[canonical_p_id] = PlayerRecord(
                        player_id=canonical_p_id,
                        full_name=p_name,
                        cricsheet_id=cric_id,
                        primary_team_id=t_id,
                        aliases=[p_name],
                    )

        def resolve_player_id(name: Optional[str]) -> Optional[str]:
            if not name:
                return None
            slug = name.lower().replace(" ", "_").replace(".", "").strip()
            p_id = f"player_{slug}"
            if p_id not in players_dict:
                # Add dynamically if not in squads list
                cric_id = registry_people.get(name)
                players_dict[p_id] = PlayerRecord(
                    player_id=p_id,
                    full_name=name,
                    cricsheet_id=cric_id,
                    aliases=[name],
                )
            return p_id

        # 5. Outcome & Winner
        outcome = info.get("outcome", {})
        winner_name = outcome.get("winner")
        winner_id = None
        if winner_name == team1_name:
            winner_id = team1_id
        elif winner_name == team2_name:
            winner_id = team2_id

        win_by = outcome.get("by", {})
        win_by_runs = win_by.get("runs")
        win_by_wickets = win_by.get("wickets")

        pom_list = info.get("player_of_match", [])
        pom_id = resolve_player_id(pom_list[0]) if pom_list else None

        toss = info.get("toss", {})
        toss_winner_name = toss.get("winner")
        toss_winner_id = team1_id if toss_winner_name == team1_name else (team2_id if toss_winner_name == team2_name else None)
        toss_decision = toss.get("decision")

        # 6. Deliveries Processing & Validation
        innings_raw = raw_data.get("innings", [])
        deliveries_list: List[DeliveryRecord] = []
        innings_totals: Dict[int, int] = {}
        innings_wickets: Dict[int, int] = {}
        seen_delivery_keys: Set[Tuple[int, int, int]] = set()

        target_runs: Optional[int] = None

        for inn_idx, inn in enumerate(innings_raw, start=1):
            inn_runs = 0
            inn_wkts = 0
            inn_target = inn.get("target", {}).get("runs")
            if inn_target and not target_runs:
                target_runs = inn_target

            overs_data = inn.get("overs", [])
            for over_dict in overs_data:
                over_num = over_dict.get("over")
                if over_num is None:
                    warnings.append(f"Innings {inn_idx}: Over missing 'over' index; skipped")
                    continue

                deliveries_in_over = over_dict.get("deliveries", [])
                for ball_idx, deliv_dict in enumerate(deliveries_in_over, start=1):
                    key = (inn_idx, over_num, ball_idx)
                    if key in seen_delivery_keys:
                        warnings.append(f"Duplicate delivery encountered: Innings {inn_idx}, Over {over_num}, Ball {ball_idx}")
                        continue
                    seen_delivery_keys.add(key)

                    batter_name = deliv_dict.get("batter")
                    bowler_name = deliv_dict.get("bowler")
                    non_striker_name = deliv_dict.get("non_striker")

                    batter_p_id = resolve_player_id(batter_name)
                    bowler_p_id = resolve_player_id(bowler_name)
                    non_striker_p_id = resolve_player_id(non_striker_name)

                    if not batter_p_id or not bowler_p_id:
                        warnings.append(f"Delivery missing batter/bowler at {over_num}.{ball_idx}")
                        continue

                    runs_dict = deliv_dict.get("runs", {})
                    b_runs = runs_dict.get("batter", 0)
                    e_runs = runs_dict.get("extras", 0)
                    t_runs = runs_dict.get("total", b_runs + e_runs)

                    extras_dict = deliv_dict.get("extras", {})
                    extra_type = next(iter(extras_dict.keys())) if extras_dict else None
                    is_legal = extra_type not in ("wides", "noballs")

                    wickets_list = deliv_dict.get("wickets", [])
                    is_wkt = len(wickets_list) > 0
                    w_kind = None
                    p_dismissed_id = None
                    if is_wkt:
                        w_info = wickets_list[0]
                        w_kind = w_info.get("kind")
                        p_out_name = w_info.get("player_out", batter_name)
                        p_dismissed_id = resolve_player_id(p_out_name)
                        inn_wkts += 1

                    inn_runs += t_runs
                    phase = self._determine_phase(over_num, inn_idx)

                    deliv_id = f"del_{match_id}_inn{inn_idx}_ov{over_num}_b{ball_idx}"
                    record = DeliveryRecord(
                        delivery_id=deliv_id,
                        match_id=match_id,
                        innings=inn_idx,
                        over=over_num,
                        ball=ball_idx,
                        batter_id=batter_p_id,
                        bowler_id=bowler_p_id,
                        non_striker_id=non_striker_p_id,
                        batter_runs=b_runs,
                        extra_runs=e_runs,
                        extra_type=extra_type,
                        total_runs=t_runs,
                        is_legal=is_legal,
                        is_wicket=is_wkt,
                        wicket_kind=w_kind,
                        player_dismissed_id=p_dismissed_id,
                        phase=phase,
                    )
                    deliveries_list.append(record)

            innings_totals[inn_idx] = inn_runs
            innings_wickets[inn_idx] = inn_wkts

        # 7. Score Reconciliation
        reconcile_notes: List[str] = []
        winner_reconciled = True

        if 1 in innings_totals and not target_runs:
            target_runs = innings_totals[1] + 1

        if win_by_runs is not None and 1 in innings_totals and 2 in innings_totals:
            diff = innings_totals[1] - innings_totals[2]
            if diff != win_by_runs:
                reconcile_notes.append(
                    f"Run margin mismatch: official win_by_runs={win_by_runs}, but innings diff={diff}"
                )
                winner_reconciled = False
            else:
                reconcile_notes.append(f"Score reconciled: Innings 1 ({innings_totals[1]}) - Innings 2 ({innings_totals[2]}) == {win_by_runs} runs.")

        reconciliation = ScoreReconciliationReport(
            match_id=match_id,
            innings_totals=innings_totals,
            innings_wickets=innings_wickets,
            target_runs=target_runs,
            winner_reconciled=winner_reconciled,
            reconciliation_notes=reconcile_notes,
        )

        match_record = MatchRecord(
            match_id=match_id,
            tournament=info.get("event", {}).get("name", "ICC Men's T20 World Cup"),
            season=str(info.get("season", "2024")),
            match_date=match_date,
            venue=info.get("venue", "Unknown Venue"),
            city=info.get("city"),
            team1_id=team1_id,
            team2_id=team2_id,
            toss_winner_id=toss_winner_id,
            toss_decision=toss_decision,
            winner_id=winner_id,
            win_by_runs=win_by_runs,
            win_by_wickets=win_by_wickets,
            player_of_match_id=pom_id,
            target_runs=target_runs,
            metadata={
                "match_type_number": info.get("match_type_number"),
                "stage": info.get("event", {}).get("stage"),
                "balls_per_over": info.get("balls_per_over", 6),
            },
            provenance_id=prov.provenance_id,
        )

        return CricsheetParseResult(
            match=match_record,
            teams=teams_list,
            players=list(players_dict.values()),
            deliveries=deliveries_list,
            provenance=prov,
            reconciliation=reconciliation,
            warnings=warnings,
        )

    def ingest(self, file_path: str | Path) -> CricsheetParseResult:
        return self.parse_file(file_path)
