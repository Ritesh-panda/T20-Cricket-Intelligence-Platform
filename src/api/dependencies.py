"""Dependency Injection for FastAPI Research Service.

Provides managed instances of the SQLite persistence manager, analytics
calculators, and preflight quality gate checkers with dependency override support.
"""

from __future__ import annotations

from typing import Tuple
from fastapi import Depends, Query, Request

from src.api.config import settings
from src.storage.sqlite_manager import SQLiteStorageManager
from src.analytics.preflight import AnalyticsPreflight
from src.analytics.performance import CricketPerformanceCalculator
from src.analytics.attention import MediaAttentionCalculator
from src.analytics.apdi import APDICalculator
from src.analytics.framing import NarrativeFramingCalculator


def get_storage(request: Request) -> SQLiteStorageManager:
    """Provides thread-safe SQLiteStorageManager from application state or settings."""
    if hasattr(request.app.state, "storage") and request.app.state.storage is not None:
        return request.app.state.storage
    return SQLiteStorageManager(settings.db_path)


def get_preflight(storage: SQLiteStorageManager = Depends(get_storage)) -> AnalyticsPreflight:
    """Provides AnalyticsPreflight quality checker bound to active storage."""
    return AnalyticsPreflight(storage)


def get_performance_calculator() -> CricketPerformanceCalculator:
    """Provides stateless CricketPerformanceCalculator."""
    return CricketPerformanceCalculator()


def get_attention_calculator() -> MediaAttentionCalculator:
    """Provides stateless MediaAttentionCalculator."""
    return MediaAttentionCalculator()


def get_apdi_calculator() -> APDICalculator:
    """Provides stateless APDICalculator."""
    return APDICalculator()


def get_framing_calculator() -> NarrativeFramingCalculator:
    """Provides stateless NarrativeFramingCalculator."""
    return NarrativeFramingCalculator()


def pagination_params(
    limit: int = Query(20, ge=1, le=100, description="Max items per page (1-100)"),
    offset: int = Query(0, ge=0, description="Offset starting index"),
) -> Tuple[int, int]:
    """Validates and provides standard limit/offset pagination tuple."""
    return limit, offset
