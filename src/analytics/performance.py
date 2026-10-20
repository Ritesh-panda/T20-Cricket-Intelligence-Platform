"""Cricket Performance Calculator for T20 Cricket Intelligence Platform.

Calculates objective cricket performance statistics derived strictly from
canonical match and delivery records with verified cricket scoring semantics:
- Extras (wides, no-balls, byes, leg-byes, penalty)
- Legal balls vs illegal deliveries
- Bowler-credited wickets vs non-bowler dismissals
- Powerplay, middle, and death phase breakdowns
- Role-specific transparent performance composites
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from src.analytics.schemas import CohortRole, CricketPerformanceMetrics
from src.models.canonical import WicketKind

logger = logging.getLogger("cricket_performance")

# Official cricket rules: wickets credited to the bowler
BOWLER_CREDITED_WICKETS = {
    "bowled",
    "caught",
    "caught and bowled",
    "lbw",
    "stumped",
    "hit wicket",
}


class CricketPerformanceCalculator:
    """Calculates objective cricket performance metrics for batters, bowlers, and teams."""

    VERSION = "6A.1.0"

    def compute_batter_performance(
        self,
        player_id: str,
        player_name: str,
        deliveries: List[Dict[str, Any]],
        matches_played: int,
        tournament: str = "T20 World Cup 2024",
        window_start: Optional[str] = None,
        window_end: Optional[str] = None,
    ) -> CricketPerformanceMetrics:
        """Computes batting performance for a player across deliveries faced.

        Cricket Scoring Invariants:
        - Balls faced: excludes 'wides'. Includes legal balls and 'noballs'.
        - Strike rate: (runs_scored / balls_faced) * 100.
        - Fours & Sixes: deliveries where batter_runs == 4 or 6.
        - Dismissals: deliveries where player_dismissed_id == player_id.
        """
        runs_scored = 0
        balls_faced = 0
        fours = 0
        sixes = 0
        dismissals = 0
        pp_runs = 0
        pp_balls = 0
        death_runs = 0
        death_balls = 0
        match_ids: Set[str] = set()

        for d in deliveries:
            if d.get("batter_id") != player_id:
                continue

            m_id = d.get("match_id")
            if m_id:
                match_ids.add(str(m_id))

            extra_type = d.get("extra_type")
            b_runs = int(d.get("batter_runs", 0))
            phase = str(d.get("phase", "")).lower()

            # Batter faces the ball if it is NOT a wide
            if extra_type != "wides":
                balls_faced += 1
                if phase == "powerplay":
                    pp_balls += 1
                elif phase == "death":
                    death_balls += 1

            runs_scored += b_runs
            if phase == "powerplay":
                pp_runs += b_runs
            elif phase == "death":
                death_runs += b_runs

            if b_runs == 4:
                fours += 1
            elif b_runs == 6:
                sixes += 1

        # Check dismissals where player was dismissed (could be as striker or non-striker in run outs)
        for d in deliveries:
            if d.get("player_dismissed_id") == player_id:
                dismissals += 1
                m_id = d.get("match_id")
                if m_id:
                    match_ids.add(str(m_id))

        strike_rate = round((runs_scored / balls_faced) * 100.0, 2) if balls_faced > 0 else None
        batting_avg = round(runs_scored / dismissals, 2) if dismissals > 0 else (float(runs_scored) if balls_faced > 0 else None)

        # Raw composite batting score:
        # Base runs + bonus for strike rate above 100 + boundary rewards
        sr_val = strike_rate if strike_rate is not None else 100.0
        sr_diff = max(-50.0, min(100.0, sr_val - 100.0))  # bounded impact
        raw_composite = float(runs_scored) + (0.5 * sr_diff) + (2.0 * sixes) + (1.0 * fours)

        sha_sig = hashlib.sha256(
            f"{player_id}:{tournament}:batter:{runs_scored}:{balls_faced}:{self.VERSION}".encode()
        ).hexdigest()[:10]
        metric_id = f"perf_{player_id}_bat_{sha_sig}"

        raw_stats = {
            "runs": runs_scored,
            "balls": balls_faced,
            "fours": fours,
            "sixes": sixes,
            "dismissals": dismissals,
            "strike_rate": strike_rate,
            "batting_average": batting_avg,
        }

        return CricketPerformanceMetrics(
            metric_id=metric_id,
            entity_id=player_id,
            entity_name=player_name,
            entity_type="player",
            role=CohortRole.BATTER,
            tournament=tournament,
            window_start=window_start,
            window_end=window_end,
            matches_played=max(matches_played, len(match_ids)),
            innings_count=len(match_ids) if balls_faced > 0 else 0,
            runs_scored=runs_scored,
            balls_faced=balls_faced,
            strike_rate=strike_rate,
            fours=fours,
            sixes=sixes,
            dismissals=dismissals,
            batting_average=batting_avg,
            powerplay_runs=pp_runs,
            powerplay_balls=pp_balls,
            death_runs=death_runs,
            death_balls=death_balls,
            raw_performance_composite=round(raw_composite, 2),
            match_ids=sorted(list(match_ids)),
            raw_stats_json=json.dumps(raw_stats),
            formula_version=self.VERSION,
        )

    def compute_bowler_performance(
        self,
        player_id: str,
        player_name: str,
        deliveries: List[Dict[str, Any]],
        matches_played: int,
        tournament: str = "T20 World Cup 2024",
        window_start: Optional[str] = None,
        window_end: Optional[str] = None,
    ) -> CricketPerformanceMetrics:
        """Computes bowling performance for a player across deliveries bowled.

        Cricket Scoring Invariants:
        - Legal balls: is_legal == 1.
        - Overs: legal_balls // 6 + (legal_balls % 6) / 10.
        - Runs conceded: batter_runs + (extra_runs if extra_type in ('wides', 'noballs')).
          Byes, leg-byes, and penalties are NOT charged to bowler.
        - Wickets: only BOWLER_CREDITED_WICKETS (bowled, caught, caught and bowled, lbw, stumped, hit wicket).
          Run outs and retired outs are not credited to bowler.
        - Economy: (runs_conceded * 6) / legal_balls.
        """
        legal_balls = 0
        runs_conceded = 0
        wickets_taken = 0
        wides_conceded = 0
        noballs_conceded = 0
        pp_wickets = 0
        death_wickets = 0
        match_ids: Set[str] = set()

        for d in deliveries:
            if d.get("bowler_id") != player_id:
                continue

            m_id = d.get("match_id")
            if m_id:
                match_ids.add(str(m_id))

            is_legal = bool(d.get("is_legal", 1))
            extra_type = d.get("extra_type")
            b_runs = int(d.get("batter_runs", 0))
            e_runs = int(d.get("extra_runs", 0))
            phase = str(d.get("phase", "")).lower()

            if is_legal:
                legal_balls += 1
            else:
                if extra_type == "wides":
                    wides_conceded += 1
                elif extra_type == "noballs":
                    noballs_conceded += 1

            # Bowler charges: batter runs + wides/noballs extras
            if extra_type in ("wides", "noballs"):
                runs_conceded += b_runs + e_runs
            elif extra_type in ("byes", "legbyes", "penalty"):
                runs_conceded += b_runs  # fielding extras do not charge bowler
            else:
                runs_conceded += b_runs

            # Wicket credit evaluation
            if d.get("is_wicket"):
                w_kind = str(d.get("wicket_kind", "")).lower()
                if w_kind in BOWLER_CREDITED_WICKETS:
                    wickets_taken += 1
                    if phase == "powerplay":
                        pp_wickets += 1
                    elif phase == "death":
                        death_wickets += 1

        overs_fmt = (legal_balls // 6) + ((legal_balls % 6) / 10.0)
        overs_float = legal_balls / 6.0

        economy = round((runs_conceded * 6.0) / legal_balls, 2) if legal_balls > 0 else None
        bowling_avg = round(runs_conceded / wickets_taken, 2) if wickets_taken > 0 else None
        bowling_sr = round(legal_balls / wickets_taken, 2) if wickets_taken > 0 else None

        # Raw composite bowling score:
        # 20 pts per wicket + economy bonus (relative to T20 par economy of 8.0 rpo) + 5 pts per death wicket
        econ_val = economy if economy is not None else 8.0
        econ_saving = max(0.0, (8.0 - econ_val) * overs_float)
        raw_composite = (20.0 * wickets_taken) + (2.0 * econ_saving) + (5.0 * death_wickets)

        sha_sig = hashlib.sha256(
            f"{player_id}:{tournament}:bowler:{wickets_taken}:{legal_balls}:{self.VERSION}".encode()
        ).hexdigest()[:10]
        metric_id = f"perf_{player_id}_bowl_{sha_sig}"

        raw_stats = {
            "legal_balls": legal_balls,
            "overs": overs_fmt,
            "runs_conceded": runs_conceded,
            "wickets": wickets_taken,
            "economy": economy,
            "bowling_average": bowling_avg,
            "bowling_strike_rate": bowling_sr,
            "wides": wides_conceded,
            "noballs": noballs_conceded,
        }

        return CricketPerformanceMetrics(
            metric_id=metric_id,
            entity_id=player_id,
            entity_name=player_name,
            entity_type="player",
            role=CohortRole.BOWLER,
            tournament=tournament,
            window_start=window_start,
            window_end=window_end,
            matches_played=max(matches_played, len(match_ids)),
            innings_count=len(match_ids) if legal_balls > 0 else 0,
            legal_balls_bowled=legal_balls,
            overs_bowled=overs_fmt,
            runs_conceded=runs_conceded,
            wickets_taken=wickets_taken,
            bowling_economy=economy,
            bowling_average=bowling_avg,
            bowling_strike_rate=bowling_sr,
            wides_conceded=wides_conceded,
            noballs_conceded=noballs_conceded,
            powerplay_wickets=pp_wickets,
            death_wickets=death_wickets,
            raw_performance_composite=round(raw_composite, 2),
            match_ids=sorted(list(match_ids)),
            raw_stats_json=json.dumps(raw_stats),
            formula_version=self.VERSION,
        )

    def compute_all_rounder_performance(
        self,
        player_id: str,
        player_name: str,
        deliveries: List[Dict[str, Any]],
        matches_played: int,
        tournament: str = "T20 World Cup 2024",
    ) -> CricketPerformanceMetrics:
        """Computes combined all-rounder performance."""
        bat = self.compute_batter_performance(player_id, player_name, deliveries, matches_played, tournament)
        bowl = self.compute_bowler_performance(player_id, player_name, deliveries, matches_played, tournament)

        combined_composite = (0.5 * bat.raw_performance_composite) + (0.5 * bowl.raw_performance_composite)
        combined_match_ids = sorted(list(set(bat.match_ids + bowl.match_ids)))

        sha_sig = hashlib.sha256(
            f"{player_id}:{tournament}:all_rounder:{bat.runs_scored}:{bowl.wickets_taken}:{self.VERSION}".encode()
        ).hexdigest()[:10]
        metric_id = f"perf_{player_id}_ar_{sha_sig}"

        raw_stats = {
            "batting": json.loads(bat.raw_stats_json),
            "bowling": json.loads(bowl.raw_stats_json),
        }

        return CricketPerformanceMetrics(
            metric_id=metric_id,
            entity_id=player_id,
            entity_name=player_name,
            entity_type="player",
            role=CohortRole.ALL_ROUNDER,
            tournament=tournament,
            matches_played=max(matches_played, len(combined_match_ids)),
            innings_count=bat.innings_count,
            runs_scored=bat.runs_scored,
            balls_faced=bat.balls_faced,
            strike_rate=bat.strike_rate,
            fours=bat.fours,
            sixes=bat.sixes,
            dismissals=bat.dismissals,
            batting_average=bat.batting_average,
            legal_balls_bowled=bowl.legal_balls_bowled,
            overs_bowled=bowl.overs_bowled,
            runs_conceded=bowl.runs_conceded,
            wickets_taken=bowl.wickets_taken,
            bowling_economy=bowl.bowling_economy,
            bowling_average=bowl.bowling_average,
            bowling_strike_rate=bowl.bowling_strike_rate,
            wides_conceded=bowl.wides_conceded,
            noballs_conceded=bowl.noballs_conceded,
            powerplay_runs=bat.powerplay_runs,
            death_runs=bat.death_runs,
            powerplay_wickets=bowl.powerplay_wickets,
            death_wickets=bowl.death_wickets,
            raw_performance_composite=round(combined_composite, 2),
            match_ids=combined_match_ids,
            raw_stats_json=json.dumps(raw_stats),
            formula_version=self.VERSION,
        )

    def compute_team_performance(
        self,
        team_id: str,
        team_name: str,
        matches: List[Dict[str, Any]],
        tournament: str = "T20 World Cup 2024",
    ) -> CricketPerformanceMetrics:
        """Computes team outcome and performance metrics."""
        team_matches = 0
        team_wins = 0
        match_ids: List[str] = []

        for m in matches:
            t1 = m.get("team1_id")
            t2 = m.get("team2_id")
            if team_id in (t1, t2):
                team_matches += 1
                match_ids.append(str(m.get("match_id", "")))
                winner = m.get("winner_id")
                if winner == team_id:
                    team_wins += 1

        win_pct = round((team_wins / team_matches) * 100.0, 2) if team_matches > 0 else None
        # Composite score: 25 pts per win + win rate contribution
        raw_composite = (team_wins * 25.0) + ((win_pct or 0.0) * 0.75)

        sha_sig = hashlib.sha256(
            f"{team_id}:{tournament}:team:{team_wins}:{team_matches}:{self.VERSION}".encode()
        ).hexdigest()[:10]
        metric_id = f"perf_{team_id}_team_{sha_sig}"

        return CricketPerformanceMetrics(
            metric_id=metric_id,
            entity_id=team_id,
            entity_name=team_name,
            entity_type="team",
            role=CohortRole.TEAM,
            tournament=tournament,
            matches_played=team_matches,
            team_matches=team_matches,
            team_wins=team_wins,
            win_percentage=win_pct,
            raw_performance_composite=round(raw_composite, 2),
            match_ids=match_ids,
            raw_stats_json=json.dumps({"team_matches": team_matches, "team_wins": team_wins, "win_pct": win_pct}),
            formula_version=self.VERSION,
        )
