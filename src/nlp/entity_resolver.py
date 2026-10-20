"""Multi-Signal Context-Sensitive Entity Resolution for Cricket Entities.

Separates candidate generation from ranking, scores candidates using document
and match context, and enforces strict ambiguity thresholds.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from src.nlp.gazetteer import CricketGazetteer, GazetteerEntry
from src.nlp.schemas import (
    EntityMentionRecord,
    EntityResolutionRecord,
    EntityType,
    ResolutionStatus,
)

logger = logging.getLogger(__name__)

# Configurable resolution gates
MIN_RESOLUTION_CONFIDENCE = 0.70
MIN_AMBIGUITY_MARGIN = 0.15


class EntityResolver:
    """Resolves entity mentions to canonical database IDs using contextual signals."""

    def __init__(
        self,
        gazetteer: CricketGazetteer,
        min_confidence: float = MIN_RESOLUTION_CONFIDENCE,
        ambiguity_margin: float = MIN_AMBIGUITY_MARGIN,
    ):
        self.gazetteer = gazetteer
        self.min_confidence = min_confidence
        self.ambiguity_margin = ambiguity_margin

    def resolve_mentions(
        self,
        mentions: List[EntityMentionRecord],
        document_text: str = "",
        context_teams: Optional[Set[str]] = None,
        linked_match_id: Optional[str] = None,
    ) -> Tuple[List[EntityMentionRecord], List[EntityResolutionRecord]]:
        """
        Resolves a list of mentions within a document context.
        
        Args:
            mentions: Detected entity mentions.
            document_text: Full document or paragraph text for co-occurrence cues.
            context_teams: Pre-identified teams (e.g. from match or document).
            linked_match_id: Canonical match ID if known.
            
        Returns:
            (updated_mentions, resolution_audit_records)
        """
        # Step 1: Pre-collect all team IDs mentioned in the document
        teams_in_doc: Set[str] = set(context_teams or [])
        for m in mentions:
            if m.entity_type == EntityType.TEAM and m.resolved_id:
                teams_in_doc.add(m.resolved_id)

        updated_mentions: List[EntityMentionRecord] = []
        resolution_records: List[EntityResolutionRecord] = []

        for m in mentions:
            updated_m, res_audits = self._resolve_single_mention(
                mention=m,
                teams_in_doc=teams_in_doc,
                linked_match_id=linked_match_id,
            )
            updated_mentions.append(updated_m)
            resolution_records.extend(res_audits)

        return updated_mentions, resolution_records

    def _resolve_single_mention(
        self,
        mention: EntityMentionRecord,
        teams_in_doc: Set[str],
        linked_match_id: Optional[str] = None,
    ) -> Tuple[EntityMentionRecord, List[EntityResolutionRecord]]:
        """Resolves an individual mention using multi-signal scoring."""
        surface = mention.surface_text.strip()
        candidates = self.gazetteer.lookup_alias(surface)

        if not candidates:
            # No candidates in gazetteer -> Unresolved
            return mention.model_copy(update={"resolution_status": ResolutionStatus.UNRESOLVED}), []

        # If already single unambiguous match and high confidence, verify and return
        if len(candidates) == 1 and not candidates[0].is_ambiguous:
            c = candidates[0]
            audit = EntityResolutionRecord(
                resolution_id=f"res_{mention.mention_id}_{c.canonical_id}",
                mention_id=mention.mention_id,
                candidate_id=c.canonical_id,
                entity_type=c.entity_type,
                score=0.95,
                is_winner=True,
                evidence={"signal": "unambiguous_exact_alias", "alias": c.alias_text},
            )
            updated = mention.model_copy(
                update={
                    "resolved_id": c.canonical_id,
                    "resolution_status": ResolutionStatus.RESOLVED,
                    "confidence": 0.95,
                }
            )
            return updated, [audit]

        # Multi-candidate ranking
        scored_candidates: List[tuple[GazetteerEntry, float, Dict[str, Any]]] = []

        for c in candidates:
            score = 0.0
            evidence: Dict[str, Any] = {}

            # 1. Base alias fidelity
            if surface.lower() == self.gazetteer.get_canonical_name(c.canonical_id).lower():
                score += 0.60
                evidence["canonical_name_match"] = True
            elif not c.is_ambiguous:
                score += 0.50
                evidence["unambiguous_alias"] = True
            else:
                score += 0.40
                evidence["ambiguous_alias"] = True

            # 2. Team Context Signal (+0.35)
            if c.primary_team_id and c.primary_team_id in teams_in_doc:
                score += 0.35
                evidence["team_context_matched"] = c.primary_team_id

            final_score = min(1.0, round(score, 3))
            evidence["final_score"] = final_score
            scored_candidates.append((c, final_score, evidence))

        # Sort descending by score
        scored_candidates.sort(key=lambda item: item[1], reverse=True)
        top_cand, top_score, top_evidence = scored_candidates[0]

        # Check ambiguity margin if there is a runner up
        is_ambiguous = False
        if len(scored_candidates) > 1:
            runner_up_score = scored_candidates[1][1]
            margin = top_score - runner_up_score
            top_evidence["margin_over_runner_up"] = round(margin, 3)
            if margin < self.ambiguity_margin:
                is_ambiguous = True

        # Decision
        audit_records: List[EntityResolutionRecord] = []
        if not is_ambiguous and top_score >= self.min_confidence:
            final_status = ResolutionStatus.RESOLVED
            resolved_id = top_cand.canonical_id
            final_confidence = top_score
        elif is_ambiguous:
            final_status = ResolutionStatus.AMBIGUOUS
            resolved_id = None
            final_confidence = top_score
        else:
            final_status = ResolutionStatus.UNRESOLVED
            resolved_id = None
            final_confidence = top_score

        for cand, score, ev in scored_candidates:
            is_win = (final_status == ResolutionStatus.RESOLVED and cand.canonical_id == resolved_id)
            audit_records.append(
                EntityResolutionRecord(
                    resolution_id=f"res_{mention.mention_id}_{cand.canonical_id}",
                    mention_id=mention.mention_id,
                    candidate_id=cand.canonical_id,
                    entity_type=cand.entity_type,
                    score=score,
                    is_winner=is_win,
                    evidence=ev,
                )
            )

        updated_mention = mention.model_copy(
            update={
                "resolved_id": resolved_id,
                "resolution_status": final_status,
                "confidence": final_confidence,
                "evidence": {
                    **mention.evidence,
                    "resolution_decision": final_status.value,
                    "top_score": top_score,
                    "is_ambiguous": is_ambiguous,
                },
            }
        )

        return updated_mention, audit_records
