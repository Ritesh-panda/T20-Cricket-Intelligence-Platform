"""Cricket-Specific Sentiment and Performance Framing Baselines.

Distinguishes general editorial sentiment, cricket match event polarity,
and entity-targeted performance framing (e.g. wicket is positive for bowler, adverse for batter).
Operates CPU-first using transparent, explainable lexicons and negation rules.
"""
from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional, Set, Tuple

from src.nlp.schemas import SentimentBaselineRecord, SentimentLabel

logger = logging.getLogger(__name__)

# General Lexicon
GENERAL_POSITIVE = {
    "brilliant", "outstanding", "heroic", "clutch", "masterclass", "triumph",
    "superb", "magnificent", "victory", "champion", "dominant", "excellence",
    "composed", "flawless", "thrilling", "celebrate", "stellar", "magical",
}

GENERAL_NEGATIVE = {
    "disaster", "collapse", "heartbreak", "shambolic", "costly", "blunder",
    "struggled", "failure", "dismal", "woeful", "choke", "disappointing",
    "defeated", "trouble", "erratic", "horrific", "sloppy", "shocking",
}

# Cricket Event Polarity Words
EVENT_POSITIVE_BATTING = {
    "boundary", "four", "six", "maximum", "century", "fifty", "half-century",
    "accelerated", "partnership", "finisher", "target reached",
}

EVENT_NEGATIVE_BATTING = {
    "wicket", "out", "bowled", "caught", "lbw", "run out", "stumped",
    "dismissed", "collapse", "duck", "golden duck", "maiden",
}

NEGATION_TERMS = {"not", "no", "never", "didnt", "didn't", "hardly", "barely", "failed to"}
INTENSIFIERS = {"very", "extremely", "hugely", "deeply", "immensely", "crucially", "massively"}


class CricketSentimentBaseline:
    """Explainable rule-based baseline separating general sentiment, event polarity, and entity framing."""

    def __init__(self, pipeline_version: str = "0.1.0"):
        self.pipeline_version = pipeline_version
        self._word_re = re.compile(r"\b[A-Za-z]+(?:['’\-][A-Za-z]+)*\b")

    def score_text(
        self,
        text: str,
        source_id: str,
        source_type: str = "article_paragraph",
        target_entity_id: Optional[str] = None,
        is_bowling_context: bool = False,
    ) -> SentimentBaselineRecord:
        """
        Analyzes sentiment with entity targeting and cricket event contextualization.
        
        Args:
            text: Input text span.
            source_id: Identifier of source document/paragraph.
            source_type: Type of source.
            target_entity_id: Target entity ID if aspect-focused.
            is_bowling_context: Whether target entity is the bowling/fielding side.
            
        Returns:
            SentimentBaselineRecord
        """
        if not text:
            return SentimentBaselineRecord(
                sentiment_id=f"sent_{source_id}_{target_entity_id or 'doc'}",
                source_type=source_type,
                source_id=source_id,
                target_entity_id=target_entity_id,
                general_sentiment=SentimentLabel.NEUTRAL,
                event_polarity=SentimentLabel.NEUTRAL,
                framing_score=0.0,
                compound_score=0.0,
                confidence=0.5,
                rule_applied="empty_text_neutral",
                pipeline_version=self.pipeline_version,
            )

        words = [w.lower() for w in self._word_re.findall(text)]
        evidence_tokens: List[str] = []

        # 1. General Sentiment Scoring with Negation Window
        pos_count = 0
        neg_count = 0
        window = 3

        for i, w in enumerate(words):
            # Check negation in preceding 3 words
            negated = any(words[j] in NEGATION_TERMS for j in range(max(0, i - window), i))
            intensified = any(words[j] in INTENSIFIERS for j in range(max(0, i - window), i))
            weight = 1.5 if intensified else 1.0

            if w in GENERAL_POSITIVE:
                if negated:
                    neg_count += weight
                    evidence_tokens.append(f"NOT_{w}")
                else:
                    pos_count += weight
                    evidence_tokens.append(w)
            elif w in GENERAL_NEGATIVE:
                if negated:
                    pos_count += weight
                    evidence_tokens.append(f"NOT_{w}")
                else:
                    neg_count += weight
                    evidence_tokens.append(w)

        # 2. Cricket Event Polarity
        event_bat_pos = sum(1 for w in words if w in EVENT_POSITIVE_BATTING)
        event_bat_neg = sum(1 for w in words if w in EVENT_NEGATIVE_BATTING)

        event_polarity = SentimentLabel.NEUTRAL
        if event_bat_pos > event_bat_neg:
            event_polarity = SentimentLabel.POSITIVE
        elif event_bat_neg > event_bat_pos:
            event_polarity = SentimentLabel.NEGATIVE

        # 3. Entity-Targeted Framing
        # If target is bowling side, batting negative (e.g. wickets) is POSITIVE framing for bowler!
        framing_score = 0.0
        if target_entity_id:
            if is_bowling_context:
                # Wickets taken = positive framing for bowling entity
                net_event = (event_bat_neg * 0.4) - (event_bat_pos * 0.3)
            else:
                # Runs scored = positive framing for batting entity
                net_event = (event_bat_pos * 0.4) - (event_bat_neg * 0.4)
            framing_score = max(-1.0, min(1.0, round((pos_count - neg_count) * 0.2 + net_event, 3)))
        else:
            framing_score = max(-1.0, min(1.0, round((pos_count - neg_count) * 0.25, 3)))

        # 4. Compound Score & Label
        net_sentiment = pos_count - neg_count
        compound_score = max(-1.0, min(1.0, round(net_sentiment / (pos_count + neg_count + 1e-5), 3)))

        if compound_score > 0.15:
            general_label = SentimentLabel.POSITIVE
        elif compound_score < -0.15:
            general_label = SentimentLabel.NEGATIVE
        else:
            general_label = SentimentLabel.NEUTRAL

        confidence = min(0.95, round(0.50 + 0.10 * (pos_count + neg_count + event_bat_pos + event_bat_neg), 2))

        return SentimentBaselineRecord(
            sentiment_id=f"sent_{source_id}_{target_entity_id or 'doc'}",
            source_type=source_type,
            source_id=source_id,
            target_entity_id=target_entity_id,
            general_sentiment=general_label,
            event_polarity=event_polarity,
            framing_score=framing_score,
            compound_score=compound_score,
            evidence_tokens=evidence_tokens,
            rule_applied="contextual_cricket_framing_v1",
            confidence=confidence,
            pipeline_version=self.pipeline_version,
        )
