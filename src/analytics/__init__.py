"""Phase 6A Media Attention vs Performance Analytics Package.

Exports schemas, calculators, and preflight validators for media attention metrics,
cricket performance statistics, narrative framing analysis, and the Attention-to-Performance
Discrepancy Index (APDI).
"""

from src.analytics.schemas import (
    CohortRole,
    DiscrepancyCategory,
    SufficiencyStatus,
    MediaAttentionMetrics,
    CricketPerformanceMetrics,
    NarrativeFramingMetrics,
    APDIRecord,
    PreflightCheckResult,
    AnalyticsRunRecord,
)
from src.analytics.attention import MediaAttentionCalculator
from src.analytics.performance import CricketPerformanceCalculator, BOWLER_CREDITED_WICKETS
from src.analytics.framing import NarrativeFramingCalculator
from src.analytics.apdi import APDICalculator
from src.analytics.preflight import AnalyticsPreflight

__all__ = [
    "CohortRole",
    "DiscrepancyCategory",
    "SufficiencyStatus",
    "MediaAttentionMetrics",
    "CricketPerformanceMetrics",
    "NarrativeFramingMetrics",
    "APDIRecord",
    "PreflightCheckResult",
    "AnalyticsRunRecord",
    "MediaAttentionCalculator",
    "CricketPerformanceCalculator",
    "BOWLER_CREDITED_WICKETS",
    "NarrativeFramingCalculator",
    "APDICalculator",
    "AnalyticsPreflight",
]
