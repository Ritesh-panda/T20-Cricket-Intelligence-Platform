"""Responsible Fetching Layer for T20 Cricket Intelligence.

Implements polite HTTP fetching with explicit timeouts, bounded retries with jitter,
HTTP 429 Retry-After handling, rate limiting, conditional requests (ETag / Last-Modified),
content-type checking, response size bounds, redirect domain enforcement, and robots.txt compliance.
"""
from __future__ import annotations

import email.utils
import hashlib
import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
import requests

from src.pipeline.config import SourceConfig

logger = logging.getLogger(__name__)


class FetchError(RuntimeError):
    """Base exception for all acquisition fetch failures."""
    pass


class RobotsDisallowedError(FetchError):
    """Raised when crawling a target URL is prohibited by robots.txt."""
    pass


class DisallowedRedirectError(FetchError):
    """Raised when a redirect target deviates from permitted source domains."""
    pass


class ContentTypeMismatchError(FetchError):
    """Raised when response Content-Type does not match permitted types."""
    pass


class ResponseTooLargeError(FetchError):
    """Raised when response size exceeds maximum permitted byte limit."""
    pass


@dataclass
class FetchResult:
    """Standardized result container for HTTP fetch operations."""
    url: str
    status_code: int
    content: bytes
    headers: Dict[str, str] = field(default_factory=dict)
    etag: Optional[str] = None
    last_modified: Optional[str] = None
    content_hash: str = ""
    is_not_modified: bool = False
    duration_sec: float = 0.0
    error_message: Optional[str] = None


class ResponsibleFetcher:
    """Polite, robust HTTP fetcher enforcing all ethical crawling constraints."""

    def __init__(
        self,
        user_agent: str = "T20CricketResearchBot/1.0 (+https://example.org/t20-intel)",
        session: Optional[requests.Session] = None,
    ):
        self.user_agent = user_agent
        self.session = session or requests.Session()
        self._last_request_times: Dict[str, float] = {}
        self._robots_cache: Dict[str, RobotFileParser] = {}

    def _get_rate_limiter_key(self, url: str) -> str:
        """Derives rate-limiting domain key."""
        parsed = urlparse(url)
        return parsed.netloc.lower()

    def enforce_rate_limit(self, domain_key: str, rate_limit_rps: float) -> None:
        """Enforces inter-request pause according to source rate limit."""
        if rate_limit_rps <= 0:
            return
        min_interval = 1.0 / rate_limit_rps
        now = time.time()
        last_time = self._last_request_times.get(domain_key, 0.0)
        elapsed = now - last_time
        if elapsed < min_interval:
            sleep_duration = min_interval - elapsed
            time.sleep(sleep_duration)
        self._last_request_times[domain_key] = time.time()

    def check_robots_allowed(self, url: str) -> bool:
        """Checks if URL is allowed according to domain's robots.txt directives."""
        parsed = urlparse(url)
        domain_root = f"{parsed.scheme}://{parsed.netloc}"
        if domain_root not in self._robots_cache:
            rp = RobotFileParser()
            robots_url = f"{domain_root}/robots.txt"
            try:
                headers = {"User-Agent": self.user_agent}
                resp = self.session.get(robots_url, headers=headers, timeout=5)
                if resp.status_code == 200:
                    rp.parse(resp.text.splitlines())
                else:
                    rp.allow_all = True
            except Exception as e:
                logger.warning(f"Failed to fetch robots.txt for {domain_root}: {e}; assuming polite allow")
                rp.allow_all = True
            self._robots_cache[domain_root] = rp

        return self._robots_cache[domain_root].can_fetch(self.user_agent, url)

    def _parse_retry_after(self, retry_after_header: Optional[str]) -> Optional[float]:
        """Parses HTTP 429 Retry-After header (seconds or RFC 2822 date)."""
        if not retry_after_header:
            return None
        header_val = retry_after_header.strip()
        # Case 1: Integer seconds
        try:
            return max(1.0, float(header_val))
        except ValueError:
            pass
        # Case 2: HTTP date
        try:
            parsed_date = email.utils.parsedate_to_datetime(header_val)
            now = datetime.now(timezone.utc)
            delta = (parsed_date - now).total_seconds()
            return max(1.0, delta)
        except Exception:
            return None

    def _validate_content_type(self, content_type_header: str, supported_types: List[str]) -> bool:
        """Verifies if response MIME type is supported."""
        if not supported_types:
            return True
        raw_mime = content_type_header.split(";")[0].strip().lower()
        for sup in supported_types:
            clean_sup = sup.strip().lower()
            if clean_sup in raw_mime or raw_mime in clean_sup or clean_sup == "*/*":
                return True
        return False

    def fetch(
        self,
        url: str,
        source_config: SourceConfig,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None,
    ) -> FetchResult:
        """
        Executes a polite, bounded HTTP fetch respecting conditional headers and rate limits.
        
        Args:
            url: Destination URL.
            source_config: Associated source configuration.
            etag: Previous ETag for conditional request.
            last_modified: Previous Last-Modified for conditional request.
            
        Returns:
            FetchResult object.
            
        Raises:
            RobotsDisallowedError, DisallowedRedirectError, ContentTypeMismatchError,
            ResponseTooLargeError, FetchError.
        """
        # 1. Robots.txt check
        if not self.check_robots_allowed(url):
            raise RobotsDisallowedError(f"Crawling {url} is prohibited by domain robots.txt")

        domain_key = self._get_rate_limiter_key(url)
        headers = {
            "User-Agent": self.user_agent,
            "Accept": ", ".join(source_config.supported_content_types) if source_config.supported_content_types else "*/*",
            "Accept-Encoding": "gzip, deflate",
        }
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified

        max_retries = source_config.max_retries
        max_bytes = source_config.max_response_bytes
        timeout = source_config.request_timeout_sec
        allowed_domains = source_config.allowed_domains

        start_time = time.time()
        last_error = None

        for attempt in range(1, max_retries + 2):
            self.enforce_rate_limit(domain_key, source_config.rate_limit_rps)

            try:
                # Stream response to enforce size limits and inspect redirect chain
                resp = self.session.get(
                    url,
                    headers=headers,
                    timeout=timeout,
                    stream=True,
                    allow_redirects=True,
                )

                # Validate redirects
                if resp.history:
                    for redirect_resp in resp.history:
                        redir_host = urlparse(redirect_resp.url).netloc.lower()
                        if allowed_domains and not any(redir_host == d or redir_host.endswith(f".{d}") for d in allowed_domains):
                            resp.close()
                            raise DisallowedRedirectError(
                                f"Redirect from {url} to disallowed external domain {redir_host}"
                            )

                final_host = urlparse(resp.url).netloc.lower()
                if allowed_domains and not any(final_host == d or final_host.endswith(f".{d}") for d in allowed_domains):
                    resp.close()
                    raise DisallowedRedirectError(
                        f"Final URL {resp.url} is outside permitted domains: {allowed_domains}"
                    )

                # Check 304 Not Modified
                if resp.status_code == 304:
                    resp.close()
                    duration = time.time() - start_time
                    return FetchResult(
                        url=url,
                        status_code=304,
                        content=b"",
                        headers=dict(resp.headers),
                        etag=etag,
                        last_modified=last_modified,
                        is_not_modified=True,
                        duration_sec=duration,
                    )

                # Handle 429 Too Many Requests
                if resp.status_code == 429:
                    resp.close()
                    retry_after = self._parse_retry_after(resp.headers.get("Retry-After"))
                    backoff = retry_after if retry_after else min(30.0, ((2 ** attempt) * 0.5) + random.uniform(0.1, 0.5))
                    logger.warning(f"HTTP 429 for {url}. Backing off for {backoff:.1f}s (Attempt {attempt}/{max_retries + 1})...")
                    if attempt <= max_retries:
                        time.sleep(backoff)
                        continue
                    else:
                        raise FetchError(f"HTTP 429 rate limit exceeded for {url} after {max_retries} retries")

                # Handle 5xx Server Errors
                if resp.status_code in (500, 502, 503, 504):
                    resp.close()
                    backoff = min(30.0, ((2 ** attempt) * 0.5) + random.uniform(0.1, 0.5))
                    logger.warning(f"HTTP {resp.status_code} for {url}. Retrying in {backoff:.1f}s (Attempt {attempt}/{max_retries + 1})...")
                    if attempt <= max_retries:
                        time.sleep(backoff)
                        continue
                    else:
                        raise FetchError(f"HTTP {resp.status_code} server error for {url} after {max_retries} retries")

                # Validate Content-Type
                ct_header = resp.headers.get("Content-Type", "")
                if resp.status_code == 200 and not self._validate_content_type(ct_header, source_config.supported_content_types):
                    resp.close()
                    raise ContentTypeMismatchError(
                        f"Unsupported Content-Type '{ct_header}' for {url}. Expected: {source_config.supported_content_types}"
                    )

                # Read body chunk by chunk up to max_bytes
                content_chunks = []
                bytes_read = 0
                for chunk in resp.iter_content(chunk_size=65536):
                    bytes_read += len(chunk)
                    if bytes_read > max_bytes:
                        resp.close()
                        raise ResponseTooLargeError(
                            f"Response for {url} exceeded limit of {max_bytes} bytes (received > {bytes_read} bytes)"
                        )
                    content_chunks.append(chunk)

                body_bytes = b"".join(content_chunks)
                duration = time.time() - start_time
                resp_headers = dict(resp.headers)
                content_hash = hashlib.sha256(body_bytes).hexdigest()

                return FetchResult(
                    url=url,
                    status_code=resp.status_code,
                    content=body_bytes,
                    headers=resp_headers,
                    etag=resp_headers.get("ETag"),
                    last_modified=resp_headers.get("Last-Modified"),
                    content_hash=content_hash,
                    is_not_modified=False,
                    duration_sec=duration,
                )

            except (requests.RequestException, requests.Timeout) as e:
                last_error = e
                backoff = min(30.0, ((2 ** attempt) * 0.5) + random.uniform(0.1, 0.5))
                logger.warning(f"Network error on {url}: {e}. Retrying in {backoff:.1f}s (Attempt {attempt}/{max_retries + 1})...")
                if attempt <= max_retries:
                    time.sleep(backoff)
                    continue
                else:
                    break

        raise FetchError(f"Failed to fetch {url} after {max_retries} retries: {last_error}")
