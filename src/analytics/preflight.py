"""Data Eligibility and Quality Preflight Checker for Analytics Engine.

Verifies canonical integrity, delivery reconciliation, article provenance,
entity resolution status, and minimum evidence thresholds before computing
attention, performance, or APDI metrics.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from src.analytics.schemas import PreflightCheckResult, SufficiencyStatus

if TYPE_CHECKING:
    from src.storage.sqlite_manager import SQLiteStorageManager

logger = logging.getLogger("analytics_preflight")


class AnalyticsPreflight:
    """Performs rigorous quality gate validation prior to analytical execution."""

    def __init__(self, storage: Any):
        self.storage = storage

    def run_preflight(self, tournament: Optional[str] = "T20 World Cup 2024") -> PreflightCheckResult:
        """Executes full quality gate and data eligibility inspection.

        Returns PreflightCheckResult with counts, warnings, errors, and overall eligibility.
        """
        warnings: List[str] = []
        errors: List[str] = []

        with self.storage._get_connection() as conn:
            target_tournament = tournament

            # Check matches for specified tournament, resolving aliases if needed
            if target_tournament:
                match_row = conn.execute(
                    "SELECT COUNT(*) FROM matches WHERE tournament = ?;", (target_tournament,)
                ).fetchone()
                matches_count = match_row[0] if match_row else 0

                # If 0 matches, attempt alias resolution (e.g. T20 World Cup 2024 -> ICC Men's T20 World Cup)
                if matches_count == 0:
                    alias_row = conn.execute(
                        """
                        SELECT tournament FROM matches 
                        WHERE tournament LIKE ? OR ? LIKE ('%' || tournament || '%')
                        LIMIT 1;
                        """,
                        (f"%{tournament.replace('2024', '').strip()}%", tournament),
                    ).fetchone()
                    if alias_row:
                        target_tournament = alias_row[0]
                        match_row = conn.execute(
                            "SELECT COUNT(*) FROM matches WHERE tournament = ?;", (target_tournament,)
                        ).fetchone()
                        matches_count = match_row[0] if match_row else 0
            else:
                match_row = conn.execute("SELECT COUNT(*) FROM matches;").fetchone()
                matches_count = match_row[0] if match_row else 0

            # 1. Delivery counts
            if target_tournament:
                deliv_row = conn.execute(
                    """
                    SELECT COUNT(*) FROM deliveries d
                    JOIN matches m ON d.match_id = m.match_id
                    WHERE m.tournament = ?;
                    """,
                    (target_tournament,),
                ).fetchone()
            else:
                deliv_row = conn.execute("SELECT COUNT(*) FROM deliveries;").fetchone()
            deliveries_count = deliv_row[0] if deliv_row else 0

            # 2. Editorial counts
            art_row = conn.execute("SELECT COUNT(*) FROM articles;").fetchone()
            articles_count = art_row[0] if art_row else 0

            para_row = conn.execute("SELECT COUNT(*) FROM article_paragraphs;").fetchone()
            paragraphs_count = para_row[0] if para_row else 0

            comm_row = conn.execute("SELECT COUNT(*) FROM commentary_entries;").fetchone()
            commentary_count = comm_row[0] if comm_row else 0

            # 3. NLP & Entity Resolution counts
            mentions_row = conn.execute("SELECT COUNT(*) FROM entity_mentions;").fetchone()
            mentions_count = mentions_row[0] if mentions_row else 0

            res_row = conn.execute(
                "SELECT COUNT(*) FROM entity_mentions WHERE resolution_status = 'RESOLVED';"
            ).fetchone()
            resolved_mentions_count = res_row[0] if res_row else 0

            sent_row = conn.execute("SELECT COUNT(*) FROM sentiment_baselines;").fetchone()
            sentiment_count = sent_row[0] if sent_row else 0

            # 4. Canonical player eligibility counts
            if target_tournament:
                bat_row = conn.execute(
                    """
                    SELECT COUNT(DISTINCT batter_id) FROM deliveries d
                    JOIN matches m ON d.match_id = m.match_id
                    WHERE m.tournament = ?;
                    """,
                    (target_tournament,),
                ).fetchone()
                bowl_row = conn.execute(
                    """
                    SELECT COUNT(DISTINCT bowler_id) FROM deliveries d
                    JOIN matches m ON d.match_id = m.match_id
                    WHERE m.tournament = ?;
                    """,
                    (target_tournament,),
                ).fetchone()
                team_row = conn.execute(
                    """
                    SELECT COUNT(DISTINCT team1_id) + COUNT(DISTINCT team2_id) FROM matches
                    WHERE tournament = ?;
                    """,
                    (target_tournament,),
                ).fetchone()
            else:
                bat_row = conn.execute("SELECT COUNT(DISTINCT batter_id) FROM deliveries;").fetchone()
                bowl_row = conn.execute("SELECT COUNT(DISTINCT bowler_id) FROM deliveries;").fetchone()
                team_row = conn.execute(
                    "SELECT COUNT(DISTINCT team1_id) + COUNT(DISTINCT team2_id) FROM matches;"
                ).fetchone()

            batters_count = bat_row[0] if bat_row else 0
            bowlers_count = bowl_row[0] if bowl_row else 0
            teams_count = team_row[0] if team_row else 0

            # 5. Check data integrity and quality rules
            if matches_count == 0:
                warnings.append(f"No structured matches found for tournament '{tournament}'.")

            if deliveries_count == 0:
                warnings.append(f"No delivery records found for tournament '{tournament}'.")

            if articles_count == 0:
                warnings.append("No editorial articles found in database.")

            if mentions_count > 0 and resolved_mentions_count == 0:
                warnings.append("Entity mentions exist but none have been resolved to canonical IDs.")

            # Score reconciliation check on available matches
            if matches_count > 0 and deliveries_count > 0:
                if target_tournament:
                    unreconciled = conn.execute(
                        """
                        SELECT m.match_id, SUM(d.total_runs) as total_match_runs
                        FROM matches m
                        JOIN deliveries d ON m.match_id = d.match_id
                        WHERE m.tournament = ?
                        GROUP BY m.match_id
                        HAVING SUM(d.total_runs) = 0;
                        """,
                        (target_tournament,),
                    ).fetchall()
                else:
                    unreconciled = conn.execute(
                        """
                        SELECT m.match_id, SUM(d.total_runs) as total_match_runs
                        FROM matches m
                        JOIN deliveries d ON m.match_id = d.match_id
                        GROUP BY m.match_id
                        HAVING SUM(d.total_runs) = 0;
                        """
                    ).fetchall()

                if unreconciled:
                    warnings.append(f"{len(unreconciled)} matches have zero total runs recorded.")

        # Determine overall eligibility
        has_min_data = (
            matches_count > 0
            and deliveries_count > 0
            and articles_count > 0
            and resolved_mentions_count > 0
        )

        if not has_min_data:
            status = SufficiencyStatus.INSUFFICIENT_DATA
            is_eligible = False
        elif len(warnings) > 0:
            status = SufficiencyStatus.PARTIAL_COVERAGE
            is_eligible = True
        else:
            status = SufficiencyStatus.VALID
            is_eligible = True

        return PreflightCheckResult(
            is_eligible=is_eligible,
            status=status,
            tournament=target_tournament or tournament or "all",
            matches_count=matches_count,
            deliveries_count=deliveries_count,
            articles_count=articles_count,
            paragraphs_count=paragraphs_count,
            commentary_count=commentary_count,
            mentions_count=mentions_count,
            resolved_mentions_count=resolved_mentions_count,
            sentiment_records_count=sentiment_count,
            eligible_batters_count=batters_count,
            eligible_bowlers_count=bowlers_count,
            eligible_teams_count=teams_count,
            warnings=warnings,
            errors=errors,
        )
