"""Abstract Base Source Adapter for T20 Cricket Intelligence Platform.

Defines the common adapter contract, rate limiting, polite robots.txt handling,
exponential backoff, and provenance generation.
"""
from __future__ import annotations

import hashlib
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

from src.models.canonical import SourceRecord

logger = logging.getLogger(__name__)


class BaseSourceAdapter(ABC):
    """Abstract base class for all data acquisition adapters."""

    def __init__(
        self,
        source_name: str,
        rate_limit_rps: float = 0.5,
        request_timeout_sec: int = 15,
        max_retries: int = 3,
        user_agent: str = "T20CricketResearchBot/1.0 (+https://example.org/t20-intel)",
    ):
        self.source_name = source_name
        self.rate_limit_rps = rate_limit_rps
        self.min_interval = 1.0 / rate_limit_rps if rate_limit_rps > 0 else 0.0
        self.request_timeout_sec = request_timeout_sec
        self.max_retries = max_retries
        self.user_agent = user_agent
        self._last_request_time = 0.0
        self._robots_parsers: Dict[str, RobotFileParser] = {}

    def _enforce_rate_limit(self) -> None:
        """Enforces polite token/interval delay between consecutive outbound HTTP requests."""
        if self.min_interval <= 0:
            return
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self.min_interval:
            sleep_sec = self.min_interval - elapsed
            time.sleep(sleep_sec)
        self._last_request_time = time.time()

    def is_url_allowed_by_robots(self, url: str) -> bool:
        """Checks domain robots.txt to verify crawling permission."""
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        if domain not in self._robots_parsers:
            rp = RobotFileParser()
            robots_url = f"{domain}/robots.txt"
            try:
                headers = {"User-Agent": self.user_agent}
                resp = requests.get(robots_url, headers=headers, timeout=5)
                if resp.status_code == 200:
                    rp.parse(resp.text.splitlines())
                else:
                    rp.allow_all = True
            except Exception as e:
                logger.warning(f"Could not fetch robots.txt for {domain}: {e}; assuming polite allow")
                rp.allow_all = True
            self._robots_parsers[domain] = rp

        return self._robots_parsers[domain].can_fetch(self.user_agent, url)

    def fetch_url(self, url: str) -> Tuple[int, bytes, Dict[str, str]]:
        """Polite HTTP fetch with exponential backoff and robots.txt check."""
        if not self.is_url_allowed_by_robots(url):
            raise PermissionError(f"Crawling {url} is disallowed by domain robots.txt directives.")

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            self._enforce_rate_limit()
            try:
                resp = requests.get(url, headers=headers, timeout=self.request_timeout_sec)
                if resp.status_code == 200:
                    return resp.status_code, resp.content, dict(resp.headers)
                elif resp.status_code in (429, 500, 502, 503, 504):
                    backoff = (2 ** attempt) * 0.5
                    logger.warning(f"HTTP {resp.status_code} for {url}. Retrying in {backoff:.1f}s (Attempt {attempt}/{self.max_retries})...")
                    time.sleep(backoff)
                else:
                    return resp.status_code, resp.content, dict(resp.headers)
            except requests.RequestException as e:
                last_error = e
                backoff = (2 ** attempt) * 0.5
                logger.warning(f"Network error on {url}: {e}. Retrying in {backoff:.1f}s...")
                time.sleep(backoff)

        raise RuntimeError(f"Failed to fetch {url} after {self.max_retries} attempts: {last_error}")

    def create_provenance_record(
        self,
        source_identifier: str,
        raw_bytes: bytes,
        source_url: Optional[str] = None,
        http_status: Optional[int] = None,
        license_tag: str = "Unknown",
        redistributable: bool = False,
    ) -> SourceRecord:
        """Constructs an immutable SourceRecord provenance audit trail."""
        content_hash = hashlib.sha256(raw_bytes).hexdigest()
        prov_id = f"prov_{content_hash[:10]}"
        return SourceRecord(
            provenance_id=prov_id,
            source_name=self.source_name,
            source_identifier=source_identifier,
            source_url=source_url,
            harvest_timestamp_utc=datetime.now(timezone.utc),
            http_status=http_status,
            content_hash_sha256=content_hash,
            pipeline_version="0.1.0",
            license_tag=license_tag,
            redistributable=redistributable,
        )

    @abstractmethod
    def ingest(self, *args: Any, **kwargs: Any) -> Any:
        """Abstract ingest method implemented by domain adapters."""
        pass
