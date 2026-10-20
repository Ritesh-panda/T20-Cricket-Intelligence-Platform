"""Narrative Framing and Sentiment Analysis for T20 Cricket Intelligence Platform.

Analyzes sentiment and editorial narrative framing around players and teams
separately from objective performance metrics and APDI:
- Aggregates positive, neutral, and negative framing counts
- Entity-targeted sentiment breakdown
- Publisher source-specific framing variance
- Topic cluster intersections with entities
- Traceable supporting text passages
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from src.analytics.schemas import NarrativeFramingMetrics

logger = logging.getLogger("narrative_framing")


class NarrativeFramingCalculator:
    """Analyzes sentiment and editorial narrative framing around entities."""

    VERSION = "6A.1.0"

    def compute_framing(
        self,
        entity_id: str,
        sentiments: List[Dict[str, Any]],
        paragraphs: Optional[Dict[str, Dict[str, Any]]] = None,
        articles: Optional[Dict[str, Dict[str, Any]]] = None,
        topic_assignments: Optional[List[Dict[str, Any]]] = None,
        max_samples: int = 5,
    ) -> NarrativeFramingMetrics:
        """Computes narrative framing metrics for a given entity.

        Args:
            entity_id: Canonical player or team ID.
            sentiments: Stored sentiment records where target_entity_id == entity_id or matching mentions.
            paragraphs: Mapping of paragraph_id -> paragraph dict for provenance.
            articles: Mapping of article_id -> article dict for source domain attribution.
            topic_assignments: Optional topic assignment records.
            max_samples: Number of supporting evidence snippets to preserve.
        """
        pos = 0
        neu = 0
        neg = 0

        source_breakdown: Dict[str, Dict[str, int]] = {}
        samples: List[Dict[str, Any]] = []

        paragraphs_map = paragraphs or {}
        articles_map = articles or {}

        for s in sentiments:
            label = str(s.get("general_sentiment", "")).upper()
            src_id = str(s.get("source_id", ""))

            # Attribute publisher source
            source_domain = "unknown"
            p_data = paragraphs_map.get(src_id)
            if p_data:
                art_id = p_data.get("article_id")
                art_data = articles_map.get(str(art_id)) if art_id else None
                if art_data and art_data.get("source_domain"):
                    source_domain = art_data["source_domain"]

            if source_domain not in source_breakdown:
                source_breakdown[source_domain] = {"positive": 0, "neutral": 0, "negative": 0}

            if label == "POSITIVE":
                pos += 1
                source_breakdown[source_domain]["positive"] += 1
            elif label == "NEGATIVE":
                neg += 1
                source_breakdown[source_domain]["negative"] += 1
            else:
                neu += 1
                source_breakdown[source_domain]["neutral"] += 1

            if len(samples) < max_samples and p_data:
                samples.append({
                    "paragraph_id": src_id,
                    "sentiment": label,
                    "framing_score": s.get("framing_score", 0.0),
                    "source_domain": source_domain,
                    "text_snippet": p_data.get("text", "")[:120] if p_data.get("text") else "",
                })

        total = pos + neu + neg
        net_score = round((pos - neg) / total, 3) if total > 0 else 0.0

        # Topic distribution intersection
        topic_dist: Dict[str, int] = {}
        if topic_assignments:
            for ta in topic_assignments:
                if str(ta.get("source_id")) in paragraphs_map:
                    cid = str(ta.get("cluster_id", "unassigned"))
                    topic_dist[cid] = topic_dist.get(cid, 0) + 1

        return NarrativeFramingMetrics(
            entity_id=entity_id,
            positive_count=pos,
            neutral_count=neu,
            negative_count=neg,
            total_framed_passages=total,
            net_framing_score=net_score,
            source_framing_breakdown=source_breakdown,
            topic_distribution=topic_dist,
            supporting_samples=samples,
        )
