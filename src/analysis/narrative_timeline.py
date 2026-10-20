"""
Structured narrative timeline construction and temporal dynamics tracking.
"""

from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from src.analysis.analysis_schemas import NarrativeTimelinePoint


class NarrativeTimelineEngine:
    """
    Constructs chronological timeline points tracking publication volume,
    sentiment distributions, topic shifts, and match event density.
    """

    def build_timeline(
        self,
        articles: List[Dict[str, Any]],
        match_events: Optional[List[Dict[str, Any]]] = None,
        bucket_by: str = "day",  # "day" or "match_phase"
    ) -> List[NarrativeTimelinePoint]:
        """
        Groups articles into temporal buckets and computes aggregated metrics.
        """
        match_events = match_events or []
        buckets: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        observed_counts: Dict[str, int] = defaultdict(int)
        inferred_counts: Dict[str, int] = defaultdict(int)

        for art in articles:
            raw_ts = art.get("published_at")
            if raw_ts:
                try:
                    if isinstance(raw_ts, str):
                        # Attempt parsing ISO format
                        dt = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
                    else:
                        dt = raw_ts

                    if bucket_by == "day":
                        b_key = dt.strftime("%Y-%m-%d")
                    else:
                        b_key = dt.strftime("%Y-%m-%d %H:00")
                    observed_counts[b_key] += 1
                except Exception:
                    b_key = "unknown_date"
                    inferred_counts[b_key] += 1
            else:
                b_key = "unknown_date"
                inferred_counts[b_key] += 1

            buckets[b_key].append(art)

        # Sort bucket keys (place 'unknown_date' at the end)
        sorted_keys = sorted([k for k in buckets.keys() if k != "unknown_date"])
        if "unknown_date" in buckets:
            sorted_keys.append("unknown_date")

        timeline: List[NarrativeTimelinePoint] = []

        for b_key in sorted_keys:
            arts = buckets[b_key]
            doc_count = len(arts)

            # Sentiment distribution
            sentiments = [a.get("sentiment_label", "NEUTRAL") for a in arts]
            sent_dist = dict(Counter(sentiments))
            sent_scores = [a.get("sentiment_score", 0.0) for a in arts]
            mean_sent = float(sum(sent_scores) / len(sent_scores)) if sent_scores else 0.0

            # Topics
            topic_list = [a.get("topic_label", "unassigned") for a in arts if a.get("topic_label")]
            top_topics = [
                {"topic": k, "count": v}
                for k, v in Counter(topic_list).most_common(3)
            ]

            # Entities
            all_entities = []
            for a in arts:
                all_entities.extend(a.get("entities", []))
            top_entities = [
                {"entity": k, "count": v}
                for k, v in Counter(all_entities).most_common(5)
            ]

            # Match events in this bucket
            events_count = 0
            for ev in match_events:
                ev_date = ev.get("date", "")
                if ev_date == b_key:
                    events_count += 1

            point = NarrativeTimelinePoint(
                bucket_label=b_key,
                doc_count=doc_count,
                mean_sentiment=round(mean_sent, 4),
                sentiment_distribution=sent_dist,
                top_topics=top_topics,
                top_entities=top_entities,
                match_events_count=events_count,
                observed_timestamps_count=observed_counts[b_key],
                inferred_timestamps_count=inferred_counts[b_key],
            )
            timeline.append(point)

        return timeline
