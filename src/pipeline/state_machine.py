"""Acquisition State Machine for T20 Cricket Intelligence Platform.

Defines the explicit processing lifecycle states for acquired resources,
validates legal state transitions, and enforces audit invariants.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional, Set
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ResourceState(str, Enum):
    """Explicit processing states for discovered resources."""
    DISCOVERED = "DISCOVERED"
    QUEUED = "QUEUED"
    FETCHED = "FETCHED"
    PARSED = "PARSED"
    VALIDATED = "VALIDATED"
    INGESTED = "INGESTED"
    SKIPPED = "SKIPPED"
    RETRY_PENDING = "RETRY_PENDING"
    FAILED = "FAILED"


# Legal transitions map: source_state -> set of allowed destination states
LEGAL_TRANSITIONS: Dict[ResourceState, Set[ResourceState]] = {
    ResourceState.DISCOVERED: {
        ResourceState.QUEUED,
        ResourceState.SKIPPED,
        ResourceState.FAILED,
    },
    ResourceState.QUEUED: {
        ResourceState.FETCHED,
        ResourceState.SKIPPED,
        ResourceState.RETRY_PENDING,
        ResourceState.FAILED,
    },
    ResourceState.FETCHED: {
        ResourceState.PARSED,
        ResourceState.SKIPPED,
        ResourceState.RETRY_PENDING,
        ResourceState.FAILED,
    },
    ResourceState.PARSED: {
        ResourceState.VALIDATED,
        ResourceState.SKIPPED,
        ResourceState.FAILED,
    },
    ResourceState.VALIDATED: {
        ResourceState.INGESTED,
        ResourceState.SKIPPED,
        ResourceState.FAILED,
    },
    ResourceState.RETRY_PENDING: {
        ResourceState.QUEUED,
        ResourceState.FAILED,
        ResourceState.SKIPPED,
    },
    ResourceState.FAILED: {
        ResourceState.QUEUED,  # For re-queuing / retry on resumption
    },
    ResourceState.SKIPPED: {
        ResourceState.QUEUED,  # In case forced re-crawling is requested
    },
    ResourceState.INGESTED: {
        ResourceState.QUEUED,  # In case forced re-processing is requested
    },
}


class IllegalStateTransitionError(ValueError):
    """Raised when an invalid state transition is attempted."""
    pass


def validate_transition(current_state: ResourceState | str, new_state: ResourceState | str) -> None:
    """Validates that a transition from current_state to new_state is legally permitted."""
    curr = ResourceState(current_state) if isinstance(current_state, str) else current_state
    dest = ResourceState(new_state) if isinstance(new_state, str) else new_state

    # Same state is a no-op / allowed
    if curr == dest:
        return

    allowed = LEGAL_TRANSITIONS.get(curr, set())
    if dest not in allowed:
        raise IllegalStateTransitionError(
            f"Illegal state transition from {curr.value} to {dest.value}. "
            f"Permitted destinations: {[s.value for s in allowed]}"
        )


class DiscoveredUrlRecord(BaseModel):
    """Model representing an entry in the discovered_urls tracking table."""
    url_id: str
    source_id: str
    raw_url: str
    canonical_url: str
    state: ResourceState = ResourceState.DISCOVERED
    discovered_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_attempt_at_utc: Optional[datetime] = None
    completed_at_utc: Optional[datetime] = None
    attempt_count: int = 0
    http_status: Optional[int] = None
    etag: Optional[str] = None
    last_modified: Optional[str] = None
    content_hash: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, str] = Field(default_factory=dict)
