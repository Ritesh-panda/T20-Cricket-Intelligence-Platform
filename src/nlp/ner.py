"""Hybrid Named Entity Recognition (NER) for Cricket Documents.

Extracts boundary-aware entity mentions for players, teams, tournaments, and venues
with character-exact start and end offsets, span deduplication, and confidence scores.
"""
from __future__ import annotations

import logging
from typing import List, Optional, Set
from src.nlp.gazetteer import CricketGazetteer, GazetteerEntry
from src.nlp.schemas import EntityMentionRecord, EntityType, ResolutionStatus

logger = logging.getLogger(__name__)


class CricketNER:
    """Extracts cricket entity mentions using boundary-aware gazetteer and pattern matching."""

    def __init__(self, gazetteer: CricketGazetteer, pipeline_version: str = "0.1.0"):
        self.gazetteer = gazetteer
        self.pipeline_version = pipeline_version

    def extract_mentions(
        self,
        text: str,
        source_id: str,
        source_type: str = "article_paragraph",
    ) -> List[EntityMentionRecord]:
        """
        Extracts entity mentions from input text with character offsets.
        Resolves overlapping mentions by favoring longer surface spans.
        """
        if not text:
            return []

        raw_matches = self.gazetteer.find_matches(text)
        if not raw_matches:
            return []

        # Sort matches by length descending to prioritize longer spans (e.g. "Virat Kohli" over "Kohli")
        raw_matches.sort(key=lambda m: (m[1] - m[0]), reverse=True)

        accepted_spans: List[tuple[int, int]] = []
        mentions: List[EntityMentionRecord] = []

        for start_char, end_char, surface, entries in raw_matches:
            # Check overlap with already accepted longer spans
            overlap = False
            for a_start, a_end in accepted_spans:
                if not (end_char <= a_start or start_char >= a_end):
                    overlap = True
                    break

            if overlap:
                continue

            accepted_spans.append((start_char, end_char))

            # Determine initial resolution status
            first_entry = entries[0]
            is_ambiguous = any(e.is_ambiguous for e in entries) or len(entries) > 1

            res_status = ResolutionStatus.AMBIGUOUS if is_ambiguous else ResolutionStatus.RESOLVED
            resolved_id = None if is_ambiguous else first_entry.canonical_id
            confidence = 0.70 if is_ambiguous else 0.95

            mention_id = f"men_{source_id}_{start_char}_{end_char}"
            record = EntityMentionRecord(
                mention_id=mention_id,
                source_type=source_type,
                source_id=source_id,
                entity_type=first_entry.entity_type,
                surface_text=surface,
                start_char=start_char,
                end_char=end_char,
                detection_method="boundary_gazetteer",
                confidence=confidence,
                resolved_id=resolved_id,
                resolution_status=res_status,
                evidence={
                    "candidate_ids": [e.canonical_id for e in entries],
                    "candidate_count": len(entries),
                    "is_ambiguous": is_ambiguous,
                    "matched_alias": first_entry.alias_text,
                },
                pipeline_version=self.pipeline_version,
            )
            mentions.append(record)

        # Sort mentions by appearance order (start_char)
        mentions.sort(key=lambda m: m.start_char)
        return mentions
