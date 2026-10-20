"""URL Normalization and Validation Engine for T20 Cricket Intelligence.

Provides deterministic canonical URL transformation, marketing parameter removal,
domain filtering, and stable identifier generation.
"""
from __future__ import annotations

import hashlib
import re
from typing import List, Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "msclkid",
    "ref",
    "ocid",
    "ncid",
    "ito",
    "rss",
    "curator",
    "cmpid",
    "_hsenc",
    "_hsmi",
    "mc_cid",
    "mc_eid",
}

DISCARD_FRAGMENTS = {
    "",
    "comments",
    "disclaimer",
    "header",
    "footer",
    "top",
    "main",
    "main-content",
    "respond",
}


class InvalidUrlError(ValueError):
    """Raised when a URL is malformed, unsupported, or outside permitted domains."""
    pass


def normalize_url(
    raw_url: str,
    allowed_domains: Optional[List[str]] = None,
    preserve_meaningful_params: bool = True,
) -> str:
    """
    Normalizes a URL to its canonical form while preserving resource-identifying query parameters.
    
    Args:
        raw_url: Incoming raw URL string.
        allowed_domains: Optional list of permitted domains.
        preserve_meaningful_params: Whether to retain non-tracking query parameters.
        
    Returns:
        Canonical URL string.
        
    Raises:
        InvalidUrlError: If URL is invalid, non-HTTP, or belongs to a disallowed domain.
    """
    url_str = (raw_url or "").strip()
    if not url_str:
        raise InvalidUrlError("Empty URL provided")

    try:
        parsed = urlparse(url_str)
    except Exception as e:
        raise InvalidUrlError(f"Malformed URL: {url_str} ({e})")

    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https"):
        raise InvalidUrlError(f"Unsupported scheme '{scheme}'. Only HTTP and HTTPS are permitted.")

    netloc = parsed.netloc.lower()
    if not netloc:
        raise InvalidUrlError(f"Missing host/domain in URL: {url_str}")

    # Strip default port numbers
    if netloc.endswith(":80") and scheme == "http":
        netloc = netloc[:-3]
    elif netloc.endswith(":443") and scheme == "https":
        netloc = netloc[:-4]

    # Validate allowed domains if provided
    if allowed_domains:
        domain_match = False
        for allowed in allowed_domains:
            clean_allowed = allowed.strip().lower()
            if netloc == clean_allowed or netloc.endswith(f".{clean_allowed}"):
                domain_match = True
                break
        if not domain_match:
            raise InvalidUrlError(f"Domain '{netloc}' is not in permitted domains: {allowed_domains}")

    # Normalize path: collapse multi-slashes
    path = parsed.path
    if not path:
        path = "/"
    else:
        path = re.sub(r"/{2,}", "/", path)
        if len(path) > 1 and path.endswith("/"):
            path = path.rstrip("/")

    # Normalize query parameters: strip tracking params, sort remainder
    query_parts: List[tuple[str, str]] = []
    if parsed.query and preserve_meaningful_params:
        raw_params = parse_qsl(parsed.query, keep_blank_values=True)
        filtered = [
            (k, v) for k, v in raw_params
            if k.lower() not in TRACKING_PARAMS and not k.lower().startswith("utm_")
        ]
        # Sort parameters deterministically
        filtered.sort(key=lambda pair: (pair[0], pair[1]))
        query_parts = filtered

    clean_query = urlencode(query_parts) if query_parts else ""

    # Fragment handling: strip empty or purely layout-based navigation fragments
    fragment = parsed.fragment
    if fragment and fragment.lower() in DISCARD_FRAGMENTS:
        fragment = ""

    canonical = urlunparse((scheme, netloc, path, "", clean_query, fragment))
    return canonical


def generate_url_id(canonical_url: str) -> str:
    """Generates a deterministic 16-hex hash identifier for a canonical URL."""
    hash_hex = hashlib.sha256(canonical_url.encode("utf-8")).hexdigest()[:16]
    return f"url_{hash_hex}"
