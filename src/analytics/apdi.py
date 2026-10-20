"""Attention-to-Performance Discrepancy Index (APDI) Engine.

Calculates the Attention-to-Performance Discrepancy Index:
    APDI = NormalizedAttention - NormalizedPerformance in [-1.0, +1.0]

Applies cohort-specific percentile normalization, data quality gates,
distinguishes OVER_ATTENDED, UNDER_ATTENDED, BALANCED, and INSUFFICIENT_DATA,
and preserves complete explainability and evidence lineage.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

from src.analytics.schemas import (
    APDIRecord,
    CohortRole,
    CricketPerformanceMetrics,
    DiscrepancyCategory,
    MediaAttentionMetrics,
    NarrativeFramingMetrics,
    SufficiencyStatus,
)

logger = logging.getLogger("apdi_calculator")


class APDICalculator:
    """Calculates APDI and explains media attention vs performance discrepancies."""

    VERSION = "6A.1.0"

    # Minimum thresholds for meaningful comparison
    MIN_BATTER_BALLS = 10
    MIN_BOWLER_BALLS = 12
    MIN_MATCHES = 1
    MIN_PARAGRAPHS = 1
    MIN_COHORT_SIZE = 2

    # Discrepancy classification thresholds
    OVER_ATTENDED_THRESHOLD = 0.20
    UNDER_ATTENDED_THRESHOLD = -0.20

    def compute_cohort_apdi(
        self,
        role: CohortRole,
        entities_data: List[Tuple[MediaAttentionMetrics, CricketPerformanceMetrics, Optional[NarrativeFramingMetrics]]],
        run_id: Optional[str] = None,
        tournament: str = "T20 World Cup 2024",
        comparison_window: str = "tournament_overall",
    ) -> List[APDIRecord]:
        """Computes APDI for all entities in a given cohort.

        Args:
            role: The role cohort (batter, bowler, all_rounder, team).
            entities_data: List of (attention_metrics, performance_metrics, framing_metrics) tuples.
            run_id: Execution run ID.
            tournament: Tournament filter.
            comparison_window: Time window or tournament stage.
        """
        if not run_id:
            run_id = f"apdi_run_{uuid.uuid4().hex[:8]}"

        results: List[APDIRecord] = []
        cohort_size = len(entities_data)

        # 1. Filter eligible entities for cohort normalization
        eligible_pairs: List[Tuple[int, MediaAttentionMetrics, CricketPerformanceMetrics, Optional[NarrativeFramingMetrics]]] = []
        for idx, (att, perf, framing) in enumerate(entities_data):
            is_eligible, _ = self._check_entity_eligibility(role, att, perf)
            if is_eligible:
                eligible_pairs.append((idx, att, perf, framing))

        eligible_count = len(eligible_pairs)

        # 2. Compute percentile ranks among eligible entities
        norm_att_map: Dict[int, float] = {}
        norm_perf_map: Dict[int, float] = {}

        if eligible_count >= self.MIN_COHORT_SIZE:
            # Rank by raw attention composite ascending
            sorted_by_att = sorted(eligible_pairs, key=lambda x: x[1].raw_attention_composite)
            for rank, (idx, _, _, _) in enumerate(sorted_by_att):
                norm_att_map[idx] = round(rank / (eligible_count - 1), 4)

            # Rank by raw performance composite ascending
            sorted_by_perf = sorted(eligible_pairs, key=lambda x: x[2].raw_performance_composite)
            for rank, (idx, _, _, _) in enumerate(sorted_by_perf):
                norm_perf_map[idx] = round(rank / (eligible_count - 1), 4)

        # 3. Build APDIRecord for every entity
        for idx, (att, perf, framing) in enumerate(entities_data):
            warnings: List[str] = []
            is_eligible, reasons = self._check_entity_eligibility(role, att, perf)
            warnings.extend(reasons)

            if eligible_count < self.MIN_COHORT_SIZE:
                warnings.append(
                    f"Cohort size ({eligible_count} eligible) is below minimum required ({self.MIN_COHORT_SIZE}) for statistical ranking."
                )

            # Sample size indicators
            sample_sizes = {
                "cohort_size": cohort_size,
                "eligible_cohort_size": eligible_count,
                "paragraph_count": att.paragraph_count,
                "article_reach": att.article_reach,
                "source_diversity": att.source_diversity_count,
                "matches_played": perf.matches_played,
                "balls_faced": perf.balls_faced,
                "legal_balls_bowled": perf.legal_balls_bowled,
            }

            # Lineage tracking
            lineage = {
                "attention_metric_id": att.metric_id,
                "performance_metric_id": perf.metric_id,
                "contributing_article_ids": att.article_ids,
                "contributing_paragraph_ids": att.paragraph_ids,
                "contributing_match_ids": perf.match_ids,
                "formula_version": self.VERSION,
                "calculation_notes": (
                    f"NormAttention = percentile rank in {role.value} cohort ({eligible_count} entities). "
                    f"NormPerformance = percentile rank in {role.value} cohort. "
                    "APDI = NormAttention - NormPerformance."
                ),
            }

            framing_dict = framing.model_dump() if framing else {}

            if not is_eligible or eligible_count < self.MIN_COHORT_SIZE:
                # Return INSUFFICIENT_DATA record without fabricated APDI
                record = APDIRecord(
                    record_id=f"apdi_{run_id}_{att.entity_id}",
                    run_id=run_id,
                    entity_id=att.entity_id,
                    entity_name=att.entity_name,
                    entity_type=att.entity_type,
                    role_cohort=role,
                    tournament=tournament,
                    comparison_window=comparison_window,
                    raw_attention_score=att.raw_attention_composite,
                    normalized_attention_score=None,
                    raw_performance_score=perf.raw_performance_composite,
                    normalized_performance_score=None,
                    apdi_value=None,
                    discrepancy_category=DiscrepancyCategory.INSUFFICIENT_DATA,
                    evidence_sufficiency_status=SufficiencyStatus.INSUFFICIENT_DATA,
                    sample_size_indicators=sample_sizes,
                    data_quality_warnings=warnings,
                    framing_breakdown=framing_dict,
                    evidence_lineage=lineage,
                    formula_version=self.VERSION,
                )
            else:
                norm_att = norm_att_map.get(idx, 0.5)
                norm_perf = norm_perf_map.get(idx, 0.5)
                apdi_val = round(norm_att - norm_perf, 4)

                # Classify discrepancy
                if apdi_val > self.OVER_ATTENDED_THRESHOLD:
                    cat = DiscrepancyCategory.OVER_ATTENDED
                elif apdi_val < self.UNDER_ATTENDED_THRESHOLD:
                    cat = DiscrepancyCategory.UNDER_ATTENDED
                else:
                    cat = DiscrepancyCategory.BALANCED

                status = SufficiencyStatus.VALID if not warnings else SufficiencyStatus.PARTIAL_COVERAGE

                record = APDIRecord(
                    record_id=f"apdi_{run_id}_{att.entity_id}",
                    run_id=run_id,
                    entity_id=att.entity_id,
                    entity_name=att.entity_name,
                    entity_type=att.entity_type,
                    role_cohort=role,
                    tournament=tournament,
                    comparison_window=comparison_window,
                    raw_attention_score=att.raw_attention_composite,
                    normalized_attention_score=norm_att,
                    raw_performance_score=perf.raw_performance_composite,
                    normalized_performance_score=norm_perf,
                    apdi_value=apdi_val,
                    discrepancy_category=cat,
                    evidence_sufficiency_status=status,
                    sample_size_indicators=sample_sizes,
                    data_quality_warnings=warnings,
                    framing_breakdown=framing_dict,
                    evidence_lineage=lineage,
                    formula_version=self.VERSION,
                )

            results.append(record)

        return results

    def _check_entity_eligibility(
        self,
        role: CohortRole,
        att: MediaAttentionMetrics,
        perf: CricketPerformanceMetrics,
    ) -> Tuple[bool, List[str]]:
        """Validates if an entity meets minimum evidence criteria for ranking."""
        reasons: List[str] = []

        if perf.matches_played < self.MIN_MATCHES:
            reasons.append(f"Entity has 0 recorded match appearances.")

        if att.paragraph_count < self.MIN_PARAGRAPHS:
            reasons.append(f"Entity has 0 editorial paragraphs in corpus.")

        if role == CohortRole.BATTER:
            if perf.balls_faced < self.MIN_BATTER_BALLS:
                reasons.append(
                    f"Batter faced {perf.balls_faced} balls, below minimum threshold of {self.MIN_BATTER_BALLS} balls."
                )
        elif role == CohortRole.BOWLER:
            if perf.legal_balls_bowled < self.MIN_BOWLER_BALLS:
                reasons.append(
                    f"Bowler bowled {perf.legal_balls_bowled} legal balls, below minimum threshold of {self.MIN_BOWLER_BALLS} balls."
                )
        elif role == CohortRole.TEAM:
            if perf.team_matches < self.MIN_MATCHES:
                reasons.append(f"Team has played 0 matches.")

        is_eligible = len(reasons) == 0
        return is_eligible, reasons
