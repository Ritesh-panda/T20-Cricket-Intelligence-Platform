"""Pydantic Models for Ingestion Runs, Provenance Records, and Pipeline Observability."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class IngestionRunResponse(BaseModel):
    """Ingestion pipeline run audit record."""
    run_id: str
    source_name: str
    status: str
    started_at_utc: str
    completed_at_utc: Optional[str] = None
    records_extracted: int = 0
    records_ingested: int = 0
    records_skipped: int = 0
    error_message: Optional[str] = None


class SourceRecordResponse(BaseModel):
    """Immutable harvest provenance record."""
    provenance_id: str
    source_name: str
    source_identifier: str
    source_url: Optional[str] = None
    harvest_timestamp_utc: str
    http_status: Optional[int] = None
    content_hash_sha256: str
    pipeline_version: str
    license_tag: str
    redistributable: bool


class PipelineStatsResponse(BaseModel):
    """Aggregated crawl, ingestion, and storage statistics."""
    source_id: str
    total_discovered: int
    total_attempts: int
    http_errors: int
    total_errors: int
    state_distribution: Dict[str, int] = Field(default_factory=dict)
    entity_counts: Dict[str, int] = Field(default_factory=dict)


class AnalyticsRunResponse(BaseModel):
    """Execution run metadata for APDI and analytics batches."""
    run_id: str
    status: str
    tournament: str
    entity_type: Optional[str] = None
    cohorts_analyzed: List[str] = Field(default_factory=list)
    entities_processed: int
    valid_apdi_count: int
    insufficient_data_count: int
    warnings: List[str] = Field(default_factory=list)
    started_at_utc: str
    completed_at_utc: Optional[str] = None
