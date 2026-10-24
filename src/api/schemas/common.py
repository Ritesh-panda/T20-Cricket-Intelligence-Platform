"""Common Pydantic Schemas for FastAPI Layer.

Defines generic pagination envelopes, health and readiness responses,
and global system status metadata.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PaginationMeta(BaseModel):
    """Metadata describing pagination slice and remaining items."""
    total: int = Field(ge=0, description="Total matching items across dataset")
    limit: int = Field(ge=1, le=100, description="Items requested per page")
    offset: int = Field(ge=0, description="Offset index")
    has_more: bool = Field(description="True if additional items remain")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic wrapper for paginated collections."""
    items: List[T] = Field(description="List of entities for current page")
    pagination: PaginationMeta = Field(description="Pagination metadata")

    @classmethod
    def create(cls, items: List[T], total: int, limit: int, offset: int) -> PaginatedResponse[T]:
        has_more = (offset + len(items)) < total
        return cls(
            items=items,
            pagination=PaginationMeta(
                total=total,
                limit=limit,
                offset=offset,
                has_more=has_more,
            ),
        )


class HealthResponse(BaseModel):
    """Liveness probe response."""
    status: str = Field(default="healthy", description="Application liveness status")
    version: str = Field(description="API service version")
    timestamp_utc: datetime = Field(default_factory=_utcnow)


class ReadinessResponse(BaseModel):
    """Readiness probe response verifying underlying persistence and dependencies."""
    status: str = Field(description="'ready' or 'not_ready'")
    database_accessible: bool = Field(description="Whether SQLite database connection succeeded")
    schema_version: Optional[int] = Field(default=None, description="Current database schema version")
    database_tables_count: int = Field(default=0, description="Count of initialized relational tables")
    timestamp_utc: datetime = Field(default_factory=_utcnow)


class StatusResponse(BaseModel):
    """System and research pipeline readiness and data sufficiency status."""
    pipeline_status: str = Field(description="Status of pipeline data layer ('operational', 'empty', 'degraded')")
    tournament: str = Field(description="Configured active tournament scope")
    record_counts: Dict[str, int] = Field(description="Inventory of stored canonical records")
    data_sufficiency_status: str = Field(description="'VALID', 'PARTIAL_COVERAGE', or 'INSUFFICIENT_DATA'")
    is_analytics_ready: bool = Field(description="True if minimum evidence thresholds are met to produce APDI")
    supported_capabilities: List[str] = Field(description="List of active platform capabilities")
    warnings: List[str] = Field(default_factory=list, description="Quality and coverage warnings")
    checked_at_utc: datetime = Field(default_factory=_utcnow)
