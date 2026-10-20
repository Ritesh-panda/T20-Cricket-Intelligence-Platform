"""Discovery Pipeline for T20 Cricket Intelligence.

Discovers permitted cricket resources across RSS/Atom feeds, XML sitemaps,
open dataset indices, and authorized article listing pages.
"""
from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse
import bs4

from src.pipeline.config import SourceCategory, SourceConfig
from src.pipeline.state_machine import DiscoveredUrlRecord, ResourceState
from src.pipeline.url_normalizer import InvalidUrlError, generate_url_id, normalize_url

logger = logging.getLogger(__name__)


class DiscoveryEngine:
    """Discovers resource candidates from configured discovery endpoints."""

    def __init__(self, fetch_func: Optional[Callable[[str], tuple[int, bytes, Dict[str, str]]]] = None):
        self._fetch_func = fetch_func

    def parse_rss_feed(self, xml_content: str | bytes, base_url: str = "") -> List[Dict[str, str]]:
        """Parses RSS or Atom XML content and extracts links and metadata."""
        if isinstance(xml_content, str):
            xml_bytes = xml_content.encode("utf-8")
        else:
            xml_bytes = xml_content

        results: List[Dict[str, str]] = []
        try:
            root = ET.fromstring(xml_bytes)
        except ET.ParseError as e:
            logger.warning(f"XML parse error in RSS feed: {e}")
            return results

        # 1. RSS 2.0 (<channel><item>)
        items = root.findall(".//item")
        for item in items:
            link_el = item.find("link")
            link = (link_el.text or "").strip() if link_el is not None else ""
            title_el = item.find("title")
            title = (title_el.text or "").strip() if title_el is not None else ""
            pub_date_el = item.find("pubDate")
            pub_date = (pub_date_el.text or "").strip() if pub_date_el is not None else ""

            if link:
                results.append({"url": urljoin(base_url, link), "title": title, "published_at": pub_date})

        # 2. Atom (<entry><link href="...">)
        if not items:
            # Handle Atom namespace
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            entries = root.findall(".//atom:entry", ns) or root.findall(".//entry")
            for entry in entries:
                link_el = entry.find("atom:link", ns) if ns else entry.find("link")
                if link_el is None:
                    link_el = entry.find("link")
                
                link = ""
                if link_el is not None:
                    link = link_el.attrib.get("href", "").strip() or (link_el.text or "").strip()

                title_el = entry.find("atom:title", ns) if ns else entry.find("title")
                if title_el is None:
                    title_el = entry.find("title")
                title = (title_el.text or "").strip() if title_el is not None else ""

                if link:
                    results.append({"url": urljoin(base_url, link), "title": title, "published_at": ""})

        return results

    def parse_sitemap(self, xml_content: str | bytes, base_url: str = "") -> List[Dict[str, str]]:
        """Parses standard sitemap XML or sitemapindex for resource URLs."""
        if isinstance(xml_content, str):
            xml_bytes = xml_content.encode("utf-8")
        else:
            xml_bytes = xml_content

        results: List[Dict[str, str]] = []
        try:
            root = ET.fromstring(xml_bytes)
        except ET.ParseError as e:
            logger.warning(f"XML parse error in Sitemap: {e}")
            return results

        # Strip namespace if present
        tag = root.tag
        ns = ""
        if tag.startswith("{"):
            ns = tag.split("}")[0] + "}"

        # URL set: <url><loc>
        for url_node in root.findall(f".//{ns}url"):
            loc_node = url_node.find(f"{ns}loc")
            if loc_node is not None and loc_node.text:
                loc = loc_node.text.strip()
                lastmod_node = url_node.find(f"{ns}lastmod")
                lastmod = (lastmod_node.text or "").strip() if lastmod_node is not None else ""
                results.append({"url": urljoin(base_url, loc), "lastmod": lastmod})

        # Sitemap index: <sitemap><loc>
        for sm_node in root.findall(f".//{ns}sitemap"):
            loc_node = sm_node.find(f"{ns}loc")
            if loc_node is not None and loc_node.text:
                loc = loc_node.text.strip()
                results.append({"url": urljoin(base_url, loc), "is_sitemap_index": "true"})

        return results

    def parse_html_listing(
        self,
        html_content: str | bytes,
        base_url: str,
        path_filter: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Extracts article or match links from an approved archive/listing HTML page."""
        soup = bs4.BeautifulSoup(html_content, "lxml")
        results: List[Dict[str, str]] = []
        seen: Set[str] = set()

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            if not href or href.startswith("#") or href.startswith("javascript:"):
                continue

            full_url = urljoin(base_url, href)
            if path_filter and path_filter not in full_url:
                continue

            title = a_tag.get_text().strip() or a_tag.get("title", "")
            if full_url not in seen:
                seen.add(full_url)
                results.append({"url": full_url, "title": title})

        return results

    def parse_cricsheet_index(self, html_or_text: str | bytes, base_url: str = "https://cricsheet.org") -> List[Dict[str, str]]:
        """Extracts Cricsheet dataset download zip and match links."""
        soup = bs4.BeautifulSoup(html_or_text, "lxml")
        results: List[Dict[str, str]] = []
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            if "t20" in href.lower() or href.endswith(".zip") or href.endswith(".json"):
                full_url = urljoin(base_url, href)
                results.append({"url": full_url, "title": a_tag.get_text().strip() or "Cricsheet Dataset"})
        return results

    def discover_from_source(
        self,
        source: SourceConfig,
        custom_payloads: Optional[Dict[str, bytes]] = None,
    ) -> List[DiscoveredUrlRecord]:
        """
        Executes discovery for a given source configuration.
        Uses custom_payloads for testing/fixtures if provided, otherwise uses fetch_func.
        """
        if not source.enabled:
            logger.info(f"Source {source.source_id} is disabled. Skipping discovery.")
            return []

        endpoints = source.discovery_endpoints or [source.base_url]
        discovered_urls: List[DiscoveredUrlRecord] = []
        seen_canonical: Set[str] = set()

        for endpoint in endpoints:
            logger.info(f"Discovering from endpoint: {endpoint} (Source: {source.source_id})")
            payload = None
            if custom_payloads and endpoint in custom_payloads:
                payload = custom_payloads[endpoint]
            elif self._fetch_func:
                try:
                    _, payload, _ = self._fetch_func(endpoint)
                except Exception as e:
                    logger.warning(f"Failed to fetch discovery endpoint {endpoint}: {e}")
                    continue

            if not payload:
                continue

            # Determine parser type based on endpoint or source category
            items: List[Dict[str, str]] = []
            if "rss" in endpoint or endpoint.endswith(".xml") or "feed" in endpoint:
                # Try RSS/Atom first
                items = self.parse_rss_feed(payload, base_url=endpoint)
                if not items:
                    # Fallback to sitemap
                    items = self.parse_sitemap(payload, base_url=endpoint)
            elif "sitemap" in endpoint:
                items = self.parse_sitemap(payload, base_url=endpoint)
            elif source.category == SourceCategory.STRUCTURED_DATA:
                items = self.parse_cricsheet_index(payload, base_url=endpoint)
            else:
                items = self.parse_html_listing(payload, base_url=endpoint)

            for item in items:
                raw_url = item.get("url", "")
                if not raw_url:
                    continue

                try:
                    canonical = normalize_url(
                        raw_url,
                        allowed_domains=source.allowed_domains or None,
                    )
                except InvalidUrlError as e:
                    logger.debug(f"Rejected discovered URL {raw_url}: {e}")
                    continue

                if canonical in seen_canonical:
                    continue

                seen_canonical.add(canonical)
                url_id = generate_url_id(canonical)
                record = DiscoveredUrlRecord(
                    url_id=url_id,
                    source_id=source.source_id,
                    raw_url=raw_url,
                    canonical_url=canonical,
                    state=ResourceState.DISCOVERED,
                    discovered_at_utc=datetime.now(timezone.utc),
                    metadata={"title": item.get("title", ""), "published_at": item.get("published_at", "")},
                )
                discovered_urls.append(record)

        return discovered_urls
