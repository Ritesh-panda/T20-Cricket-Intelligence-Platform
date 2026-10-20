"""Media Attention Calculator for T20 Cricket Intelligence Platform.

Calculates transparent, inspectable media attention metrics across:
- Mention volume (distinct paragraphs vs raw occurrences)
- Article reach within available editorial corpus
- Source publisher diversity
- Position prominence (headline vs lead paragraph vs body)
- Event-linked editorial passages
- Temporal distribution (pre-match, during-match, post-match)
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from src.analytics.schemas import MediaAttentionMetrics

logger = logging.getLogger("media_attention")


class MediaAttentionCalculator:
    """Calculates granular media attention metrics for cricket entities."""

    VERSION = "6A.1.0"

    def __init__(self, prominence_weights: Optional[Dict[str, float]] = None):
        # Weights for headline, lead paragraph, body paragraph
        self.prominence_weights = prominence_weights or {
            "headline": 3.0,
            "lead": 1.5,
            "body": 1.0,
        }

    def compute_for_entity(
        self,
        entity_id: str,
        entity_name: str,
        entity_type: str,
        mentions: List[Dict[str, Any]],
        paragraphs: Dict[str, Dict[str, Any]],
        articles: Dict[str, Dict[str, Any]],
        event_alignments: Optional[List[Dict[str, Any]]] = None,
        tournament: str = "T20 World Cup 2024",
        window_start: Optional[str] = None,
        window_end: Optional[str] = None,
        match_dates: Optional[Dict[str, str]] = None,
    ) -> MediaAttentionMetrics:
        """Computes full media attention metrics for a single canonical entity.

        Args:
            entity_id: Canonical player or team ID.
            entity_name: Display name.
            entity_type: 'player' or 'team'.
            mentions: List of resolved entity mention dicts where resolved_id == entity_id.
            paragraphs: Mapping of paragraph_id -> paragraph dict (containing article_id, paragraph_index, is_lead, etc.)
            articles: Mapping of article_id -> article dict (containing published_at_utc, source_domain, headline)
            event_alignments: Optional accepted event alignments linked to this entity or match events.
            tournament: Tournament scope.
            window_start: Optional window start timestamp.
            window_end: Optional window end timestamp.
            match_dates: Optional mapping of match_id -> match_date for temporal analysis.
        """
        raw_mention_count = len(mentions)

        # 4A & 4B: Distinct paragraphs & distinct articles
        seen_paragraph_ids: Set[str] = set()
        seen_article_ids: Set[str] = set()
        sources_seen: Set[str] = set()
        headline_article_ids: Set[str] = set()
        lead_paragraph_ids: Set[str] = set()
        body_paragraph_ids: Set[str] = set()

        temporal_dist: Dict[str, int] = {
            "pre_match": 0,
            "during_match": 0,
            "post_match": 0,
            "date_only": 0,
        }

        for m in mentions:
            src_type = m.get("source_type")
            src_id = m.get("source_id")

            # Check if mention is directly in article headline or a paragraph
            if src_type == "article" or "headline" in str(src_id).lower():
                headline_article_ids.add(str(src_id))
                seen_article_ids.add(str(src_id))
                art = articles.get(str(src_id))
                if art and art.get("source_domain"):
                    sources_seen.add(art["source_domain"])
                continue

            # Otherwise, mention is in a paragraph
            p_id = str(src_id)
            seen_paragraph_ids.add(p_id)

            p_data = paragraphs.get(p_id, {})
            art_id = p_data.get("article_id")
            if art_id:
                seen_article_ids.add(str(art_id))
                art = articles.get(str(art_id), {})
                if art and art.get("source_domain"):
                    sources_seen.add(art["source_domain"])

                # Prominence evaluation
                seq_idx = p_data.get("sequence_index", p_data.get("paragraph_index", 1))
                is_lead = p_data.get("is_lead", False) or seq_idx == 0

                if is_lead:
                    lead_paragraph_ids.add(p_id)
                else:
                    body_paragraph_ids.add(p_id)

                # Temporal evaluation if article publication timestamp is available
                pub_time_str = art.get("published_at_utc")
                if pub_time_str and match_dates:
                    self._bucket_temporal(pub_time_str, match_dates, temporal_dist)
                elif pub_time_str:
                    temporal_dist["date_only"] += 1
            else:
                body_paragraph_ids.add(p_id)

        headline_count = len(headline_article_ids)
        lead_count = len(lead_paragraph_ids)
        body_count = len(body_paragraph_ids)

        # 4D: Prominence calculation
        prominence_score = (
            headline_count * self.prominence_weights["headline"]
            + lead_count * self.prominence_weights["lead"]
            + body_count * self.prominence_weights["body"]
        )

        # 4E: Event-related attention (accepted narrative-to-event links)
        event_linked_count = 0
        if event_alignments:
            for ea in event_alignments:
                # Link is accepted if status is ACCEPTED
                status = ea.get("status")
                if status == "ACCEPTED":
                    # Check if paragraph is in seen_paragraph_ids or matches entity
                    p_id = ea.get("paragraph_id", ea.get("editorial_norm_id"))
                    if p_id in seen_paragraph_ids:
                        event_linked_count += 1

        # Transparent raw attention composite:
        # Paragraph volume (weight 1.0) + Article reach (weight 2.0) + Source diversity (weight 1.5) + Prominence bonus
        # Prominence bonus is extra weight for headline and lead paragraphs
        prominence_bonus = (headline_count * 2.0) + (lead_count * 1.0)
        raw_composite = (
            (len(seen_paragraph_ids) * 1.0)
            + (len(seen_article_ids) * 2.0)
            + (len(sources_seen) * 1.5)
            + prominence_bonus
        )

        # Deterministic metric_id
        sha_sig = hashlib.sha256(
            f"{entity_id}:{tournament}:{len(seen_paragraph_ids)}:{raw_mention_count}:{self.VERSION}".encode()
        ).hexdigest()[:10]
        metric_id = f"att_{entity_id}_{sha_sig}"

        return MediaAttentionMetrics(
            metric_id=metric_id,
            entity_id=entity_id,
            entity_name=entity_name,
            entity_type=entity_type,
            tournament=tournament,
            window_start=window_start,
            window_end=window_end,
            paragraph_count=len(seen_paragraph_ids),
            raw_mention_count=raw_mention_count,
            article_reach=len(seen_article_ids),
            source_diversity_count=len(sources_seen),
            sources=sorted(list(sources_seen)),
            prominence_score=round(prominence_score, 2),
            headline_mentions=headline_count,
            lead_paragraph_mentions=lead_count,
            body_paragraph_mentions=body_count,
            event_linked_mentions=event_linked_count,
            temporal_distribution=temporal_dist,
            article_ids=sorted(list(seen_article_ids)),
            paragraph_ids=sorted(list(seen_paragraph_ids)),
            raw_attention_composite=round(raw_composite, 2),
            formula_version=self.VERSION,
        )

    def _bucket_temporal(
        self,
        pub_time_str: str,
        match_dates: Dict[str, str],
        temporal_dist: Dict[str, int],
    ) -> None:
        """Assigns publication date/time to pre-match, during-match, or post-match."""
        try:
            pub_dt = datetime.fromisoformat(pub_time_str.replace("Z", "+00:00"))
            pub_date_str = pub_dt.strftime("%Y-%m-%d")

            # Check matches on this date or surrounding dates
            matched_temporal = False
            for m_id, m_date in match_dates.items():
                if pub_date_str == m_date:
                    temporal_dist["during_match"] += 1
                    matched_temporal = True
                    break
                elif pub_date_str < m_date:
                    temporal_dist["pre_match"] += 1
                    matched_temporal = True
                    break
                else:
                    temporal_dist["post_match"] += 1
                    matched_temporal = True
                    break
            if not matched_temporal:
                temporal_dist["date_only"] += 1
        except Exception:
            temporal_dist["date_only"] += 1
