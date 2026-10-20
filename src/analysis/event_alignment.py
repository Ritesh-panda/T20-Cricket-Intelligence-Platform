"""
Event alignment engine linking editorial narrative segments to structured match milestones.
"""

from typing import Any, Dict, List, Optional, Set


class EventAlignmentEngine:
    """
    Identifies structured match milestones (e.g. powerplay finish, death overs, wickets)
    and evaluates evidence-backed alignments with editorial paragraphs.
    """

    def synthesize_match_milestones(self, deliveries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Synthesizes structured match deliveries into notable milestones.
        """
        milestones = []
        if not deliveries:
            return milestones

        # Group deliveries by over
        overs: Dict[int, List[Dict[str, Any]]] = {}
        for d in deliveries:
            ov = d.get("over_number", 0)
            if ov not in overs:
                overs[ov] = []
            overs[ov].append(d)

        for ov, delivs in overs.items():
            # 1. Wicket events
            wickets = [d for d in delivs if d.get("is_wicket", False)]
            if wickets:
                bowler = wickets[0].get("bowler_id", "bowler")
                batter = wickets[0].get("player_dismissed_id", "batter")
                milestones.append({
                    "milestone_type": "WICKET",
                    "over_number": ov,
                    "innings_num": delivs[0].get("innings_num", 1),
                    "primary_actors": [bowler, batter],
                    "description": f"Wicket in over {ov}: {bowler} dismissed {batter}",
                })

            # 2. High-scoring boundary overs (e.g., >= 15 runs)
            over_runs = sum(d.get("total_runs", 0) for d in delivs)
            if over_runs >= 15:
                milestones.append({
                    "milestone_type": "EXPENSIVE_OVER",
                    "over_number": ov,
                    "innings_num": delivs[0].get("innings_num", 1),
                    "runs_conceded": over_runs,
                    "description": f"Over {ov} yielded {over_runs} runs",
                })

            # 3. Maiden / tight death over (e.g., over 19 or 20 yielding <= 4 runs)
            if ov in (19, 20) and over_runs <= 4:
                bowler = delivs[0].get("bowler_id", "bowler")
                milestones.append({
                    "milestone_type": "DEATH_OVER_EXECUTION",
                    "over_number": ov,
                    "innings_num": delivs[0].get("innings_num", 1),
                    "primary_actors": [bowler],
                    "description": f"Clinical death over {ov} by {bowler}: {over_runs} runs conceded",
                })

        return milestones

    def align_editorial_to_milestones(
        self,
        paragraph_id: str,
        paragraph_text: str,
        paragraph_entities: Set[str],
        milestones: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Evaluates heuristic alignment between an editorial paragraph and match milestones.
        """
        alignments = []
        text_lower = paragraph_text.lower()

        for m in milestones:
            actors = m.get("primary_actors", [])
            shared_actors = set(actors).intersection(paragraph_entities)
            m_type = m["milestone_type"]

            score = 0.0
            evidence = {
                "milestone_type": m_type,
                "over_number": m["over_number"],
                "shared_actors": list(shared_actors),
            }

            if shared_actors:
                score += 0.50

            # Keyword signals
            if m_type == "WICKET" and any(k in text_lower for k in ["wicket", "dismissed", "out", "caught", "bowled"]):
                score += 0.30
                evidence["keyword_match"] = "wicket_terminology"
            elif m_type == "DEATH_OVER_EXECUTION" and any(k in text_lower for k in ["death", "yorker", "final over", "19th", "20th"]):
                score += 0.35
                evidence["keyword_match"] = "death_overs_terminology"
            elif m_type == "EXPENSIVE_OVER" and any(k in text_lower for k in ["six", "boundary", "expensive", "hammered"]):
                score += 0.25
                evidence["keyword_match"] = "expensive_over_terminology"

            if score >= 0.50:
                alignments.append({
                    "paragraph_id": paragraph_id,
                    "milestone": m,
                    "alignment_confidence": round(score, 3),
                    "evidence": evidence,
                })

        alignments.sort(key=lambda x: x["alignment_confidence"], reverse=True)
        return alignments
