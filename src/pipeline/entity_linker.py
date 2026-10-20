"""Match and Player Linking Engine for T20 Cricket Intelligence.

Provides conservative, evidence-backed entity resolution linking unstructured
articles and commentary to canonical match, team, and player records.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from src.storage.sqlite_manager import SQLiteStorageManager

logger = logging.getLogger(__name__)

# Minimum confidence required to establish a canonical match link
MIN_LINKING_CONFIDENCE = 0.65
AMBIGUITY_MARGIN = 0.15


@dataclass
class MatchLinkCandidate:
    """Resolved candidate link between an unstructured text and a canonical match."""
    match_id: str
    confidence: float
    evidence: Dict[str, Any] = field(default_factory=dict)


class EntityLinker:
    """Conservative entity resolution engine linking texts to ground-truth matches."""

    def __init__(self, storage: SQLiteStorageManager):
        self.storage = storage
        self._teams_cache: List[Dict[str, Any]] = []
        self._matches_cache: List[Dict[str, Any]] = []
        self._refresh_caches()

    def _refresh_caches(self) -> None:
        """Loads canonical teams and matches into memory for fast lookup."""
        with self.storage._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT team_id, name, aliases_json FROM teams;")
            self._teams_cache = [
                {
                    "team_id": row["team_id"],
                    "name": row["name"],
                    "aliases": [row["name"].lower()] + [a.lower() for a in eval(row["aliases_json"] or "[]")],
                }
                for row in cursor.fetchall()
            ]

            cursor.execute("SELECT match_id, tournament, match_date, venue, city, team1_id, team2_id FROM matches;")
            self._matches_cache = [dict(row) for row in cursor.fetchall()]

    def extract_mentioned_teams(self, text: str) -> List[str]:
        """Finds all canonical team IDs mentioned in text."""
        text_lower = text.lower()
        matched_teams = []
        for team in self._teams_cache:
            for alias in team["aliases"]:
                # Use word boundaries to avoid substring false matches
                pattern = rf"\b{re.escape(alias)}\b"
                if re.search(pattern, text_lower):
                    matched_teams.append(team["team_id"])
                    break
        return matched_teams

    def resolve_match_link(
        self,
        headline: str,
        full_text: str,
        published_at_utc: Optional[datetime] = None,
    ) -> Optional[MatchLinkCandidate]:
        """
        Conservatively resolves an article or commentary excerpt to a canonical match.
        Returns None if no candidate satisfies the strict confidence threshold.
        """
        if not self._matches_cache:
            self._refresh_caches()
            if not self._matches_cache:
                return None

        combined_text = f"{headline}\n{full_text}"
        combined_lower = combined_text.lower()
        teams_found = set(self.extract_mentioned_teams(combined_text))

        candidates: List[MatchLinkCandidate] = []

        for m in self._matches_cache:
            score = 0.0
            evidence: Dict[str, Any] = {
                "teams_matched": [],
                "date_proximity_days": None,
                "tournament_matched": False,
                "venue_matched": False,
            }

            # 1. Team matching
            t1 = m["team1_id"]
            t2 = m["team2_id"]
            t1_found = t1 in teams_found
            t2_found = t2 in teams_found

            if t1_found and t2_found:
                score += 0.45
                evidence["teams_matched"] = [t1, t2]
            elif t1_found or t2_found:
                score += 0.10
                evidence["teams_matched"] = [t1 if t1_found else t2]

            # 2. Date proximity
            if published_at_utc and m["match_date"]:
                try:
                    m_date = datetime.strptime(m["match_date"], "%Y-%m-%d").date()
                    pub_date = published_at_utc.date()
                    delta_days = abs((pub_date - m_date).days)
                    evidence["date_proximity_days"] = delta_days

                    if delta_days == 0:
                        score += 0.35
                    elif delta_days == 1:
                        score += 0.25
                    elif delta_days <= 3:
                        score += 0.15
                    elif delta_days > 7:
                        # Heavy penalty if publication is weeks away from match
                        score -= 0.20
                except Exception:
                    pass

            # 3. Tournament mention
            tournament_str = m.get("tournament", "").lower()
            if tournament_str and tournament_str in combined_lower:
                score += 0.15
                evidence["tournament_matched"] = True
            elif "t20 world cup" in combined_lower:
                score += 0.10
                evidence["tournament_matched"] = True

            # 4. Venue or City mention
            venue_str = m.get("venue", "").lower()
            city_str = (m.get("city") or "").lower()
            if venue_str and len(venue_str) > 4 and venue_str in combined_lower:
                score += 0.10
                evidence["venue_matched"] = True
            elif city_str and len(city_str) > 3 and city_str in combined_lower:
                score += 0.05
                evidence["venue_matched"] = True

            final_score = max(0.0, min(1.0, score))
            if final_score >= MIN_LINKING_CONFIDENCE:
                candidates.append(
                    MatchLinkCandidate(
                        match_id=m["match_id"],
                        confidence=round(final_score, 3),
                        evidence=evidence,
                    )
                )

        if not candidates:
            return None

        # Sort candidates by descending confidence
        candidates.sort(key=lambda c: c.confidence, reverse=True)
        top_candidate = candidates[0]

        # Check for ambiguity: if second candidate is too close, reject both!
        if len(candidates) > 1:
            second_candidate = candidates[1]
            if (top_candidate.confidence - second_candidate.confidence) < AMBIGUITY_MARGIN:
                logger.info(
                    f"Ambiguous match link for headline '{headline[:40]}...': "
                    f"Candidate 1 ({top_candidate.match_id}: {top_candidate.confidence}) vs "
                    f"Candidate 2 ({second_candidate.match_id}: {second_candidate.confidence}). Leaving unresolved."
                )
                return None

        return top_candidate
