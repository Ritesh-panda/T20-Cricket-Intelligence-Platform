"""Source Registry and Configuration for T20 Cricket Intelligence Platform.

Provides strongly-typed Pydantic configuration schemas for all data sources,
enforcing polite crawl policies, retention constraints, and adapter mappings.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class SourceCategory(str, Enum):
    STRUCTURED_DATA = "structured_data"
    COMMENTARY = "commentary"
    NEWS = "news"
    RSS = "rss"
    SITEMAP = "sitemap"
    API = "api"


class RetentionPolicy(BaseModel):
    """Data retention and redistribution constraints."""
    store_full_text: bool = Field(default=False, description="Whether full text can be legally stored")
    store_summary_only: bool = Field(default=True, description="Whether only summary and metadata are kept")
    redistributable: bool = Field(default=False, description="Whether content is redistributable")
    retention_days: Optional[int] = Field(default=None, description="Max retention days if bounded")


class SourceConfig(BaseModel):
    """Configuration record for an individual data source."""
    source_id: str = Field(description="Stable unique source identifier")
    name: str = Field(description="Human-readable source name")
    category: SourceCategory = Field(description="Type of source")
    base_url: str = Field(description="Root URL or download endpoint")
    discovery_endpoints: List[str] = Field(default_factory=list, description="Permitted discovery URLs / feeds")
    adapter_id: str = Field(description="Identifier for adapter: cricsheet, commentary, news")
    enabled: bool = Field(default=False, description="Whether source is actively enabled")
    rate_limit_rps: float = Field(default=0.5, ge=0.0, le=5.0, description="Polite rate limit in requests per second")
    request_timeout_sec: int = Field(default=15, ge=1, le=120, description="Read/connect timeout in seconds")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts on 429/5xx")
    max_response_bytes: int = Field(default=10 * 1024 * 1024, description="Max allowed response size in bytes")
    supported_content_types: List[str] = Field(
        default_factory=lambda: ["text/html", "application/xhtml+xml"],
        description="Allowed MIME types for responses"
    )
    retention_policy: RetentionPolicy = Field(default_factory=RetentionPolicy)
    license_tag: str = Field(default="Unknown", description="Declared data license")
    licence_notes: str = Field(default="", description="Licensing and terms compliance notes")
    allowed_domains: List[str] = Field(default_factory=list, description="Domains permitted for redirects/crawling")
    last_successful_crawl_utc: Optional[datetime] = None
    last_attempted_crawl_utc: Optional[datetime] = None
    custom_metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("source_id")
    @classmethod
    def validate_source_id(cls, v: str) -> str:
        v_clean = v.strip().lower()
        if not v_clean:
            raise ValueError("source_id cannot be empty")
        return v_clean


class SourceRegistry:
    """Manages loaded source configurations with YAML loading and queries."""

    def __init__(self, config_path: str | Path):
        self.config_path = Path(config_path)
        self.sources: Dict[str, SourceConfig] = {}
        self.load()

    def load(self) -> None:
        """Loads and parses source configurations from the YAML configuration file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Source configuration file not found at {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            raw_yaml = yaml.safe_load(f) or {}

        sources_data = raw_yaml.get("sources", {})
        self.sources.clear()

        for source_key, data in sources_data.items():
            # If source_id is not explicitly in dict, use the key
            if "source_id" not in data:
                data["source_id"] = source_key
            if "name" not in data:
                data["name"] = data.get("domain", source_key).capitalize()
            
            # Map legacy/convenience category types if needed
            cat_map = {
                "open_dataset": SourceCategory.STRUCTURED_DATA,
                "publisher_news": SourceCategory.NEWS,
                "publisher_news_and_commentary": SourceCategory.COMMENTARY,
                "publisher_editorial": SourceCategory.NEWS,
                "rss": SourceCategory.RSS,
                "sitemap": SourceCategory.SITEMAP,
                "api": SourceCategory.API,
                "structured_data": SourceCategory.STRUCTURED_DATA,
                "commentary": SourceCategory.COMMENTARY,
                "news": SourceCategory.NEWS,
            }
            raw_type = data.get("category") or data.get("type", "news")
            if isinstance(raw_type, str) and raw_type in cat_map:
                data["category"] = cat_map[raw_type]

            # Adapter ID mapping fallback
            if "adapter_id" not in data:
                if data["category"] == SourceCategory.STRUCTURED_DATA:
                    data["adapter_id"] = "cricsheet"
                elif data["category"] == SourceCategory.COMMENTARY:
                    data["adapter_id"] = "commentary"
                else:
                    data["adapter_id"] = "news"

            # Populate discovery endpoints from legacy fields if needed
            discovery = list(data.get("discovery_endpoints", []))
            if "sitemap_url" in data and data["sitemap_url"] not in discovery:
                discovery.append(data["sitemap_url"])
            if "rss_url" in data and data["rss_url"] not in discovery:
                discovery.append(data["rss_url"])
            data["discovery_endpoints"] = discovery

            # Populate allowed domains
            allowed = list(data.get("allowed_domains", []))
            if "domain" in data and data["domain"] not in allowed:
                allowed.append(data["domain"])
            data["allowed_domains"] = allowed

            # Retention policy normalization
            if "retention_policy" not in data:
                is_open = (data["category"] == SourceCategory.STRUCTURED_DATA)
                data["retention_policy"] = RetentionPolicy(
                    store_full_text=is_open,
                    store_summary_only=not is_open,
                    redistributable=is_open,
                )

            # License normalization
            if "license_tag" not in data:
                data["license_tag"] = "ODbL-1.0" if data["category"] == SourceCategory.STRUCTURED_DATA else "FairUse-ResearchExtraction"

            # Supported content types
            if "supported_content_types" not in data:
                if data["category"] == SourceCategory.STRUCTURED_DATA:
                    data["supported_content_types"] = ["application/json", "application/zip"]
                else:
                    data["supported_content_types"] = [
                        "text/html",
                        "application/xhtml+xml",
                        "text/xml",
                        "application/xml",
                        "application/rss+xml",
                    ]

            source_cfg = SourceConfig(**data)
            self.sources[source_cfg.source_id] = source_cfg

    def get_source(self, source_id: str) -> Optional[SourceConfig]:
        """Retrieves a source configuration by its stable ID."""
        return self.sources.get(source_id.strip().lower())

    def list_sources(self, enabled_only: bool = False) -> List[SourceConfig]:
        """Lists all registered sources, optionally filtering for enabled only."""
        if enabled_only:
            return [s for s in self.sources.values() if s.enabled]
        return list(self.sources.values())

    def update_crawl_timestamps(
        self,
        source_id: str,
        attempted_at: Optional[datetime] = None,
        succeeded_at: Optional[datetime] = None,
    ) -> None:
        """Updates in-memory crawl timestamps for a source."""
        source = self.get_source(source_id)
        if not source:
            return
        if attempted_at:
            source.last_attempted_crawl_utc = attempted_at
        if succeeded_at:
            source.last_successful_crawl_utc = succeeded_at
