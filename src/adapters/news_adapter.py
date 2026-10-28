"""News Ingestion Adapter for T20 Cricket Intelligence Platform.

Extracts main body text, headline, byline, and publication date from permitted
cricket journalism pages using Trafilatura with BeautifulSoup4 fallback.
Splits text into discrete paragraph records for downstream NER and event alignment.
"""
from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import bs4
import trafilatura

from src.adapters.base import BaseSourceAdapter
from src.models.canonical import ArticleParagraphRecord, ArticleRecord, SourceRecord

logger = logging.getLogger(__name__)


class NewsArticleAdapter(BaseSourceAdapter):
    """Adapter for permitted editorial news, match previews, and post-match reviews."""

    def __init__(self, rate_limit_rps: float = 0.5, request_timeout_sec: int = 15):
        super().__init__(
            source_name="publisher_news",
            rate_limit_rps=rate_limit_rps,
            request_timeout_sec=request_timeout_sec,
            user_agent="T20CricketResearchBot/1.0 (+https://example.org/t20-intel)",
        )

    def _extract_fallback_metadata(self, html_text: str) -> Tuple[str, Optional[str], Optional[datetime]]:
        """Fallback DOM extraction using BeautifulSoup for title, author, and date."""
        soup = bs4.BeautifulSoup(html_text, "lxml")
        
        # 1. Title / Headline
        headline = None
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            headline = str(og_title["content"]).strip()
        elif soup.title and soup.title.string:
            headline = str(soup.title.string).strip()
        elif soup.find("h1"):
            headline = soup.find("h1").get_text().strip()
        else:
            headline = "Untitled Cricket Report"

        # 2. Author
        author = None
        meta_author = soup.find("meta", attrs={"name": "author"}) or soup.find("meta", property="article:author")
        if meta_author and meta_author.get("content"):
            author = str(meta_author["content"]).strip()

        # 3. Date
        published_at = None
        time_tag = soup.find("time")
        if time_tag and time_tag.get("datetime"):
            dt_str = str(time_tag["datetime"])
            try:
                # Handle ISO 8601 with Z or offset
                published_at = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            except Exception:
                pass

        return headline, author, published_at

    def parse_html(
        self,
        html_content: str | bytes,
        canonical_url: str,
        source_domain: Optional[str] = None,
    ) -> Tuple[ArticleRecord, List[ArticleParagraphRecord], SourceRecord]:
        """
        Parses raw HTML payload into canonical ArticleRecord and ArticleParagraphRecords.
        Enforces strict text extraction and provenance generation.
        """
        if isinstance(html_content, str):
            raw_bytes = html_content.encode("utf-8")
            html_text = html_content
        else:
            raw_bytes = html_content
            html_text = html_content.decode("utf-8", errors="replace")

        if not source_domain:
            source_domain = urlparse(canonical_url).netloc or "unknown_domain"

        # 1. Provenance
        prov = self.create_provenance_record(
            source_identifier=canonical_url,
            raw_bytes=raw_bytes,
            source_url=canonical_url,
            license_tag="FairUse-ResearchExtraction",
            redistributable=False,
        )

        # 2. Extract content with Trafilatura
        extracted_text = trafilatura.extract(
            html_text,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
            output_format="txt",
        )
        extracted_meta = trafilatura.extract_metadata(html_text)

        headline = None
        author = None
        published_at = None

        if extracted_meta:
            headline = extracted_meta.title
            author = extracted_meta.author
            if extracted_meta.date:
                try:
                    published_at = datetime.fromisoformat(extracted_meta.date).replace(tzinfo=timezone.utc)
                except Exception:
                    pass

        # 3. Fallbacks if Trafilatura missed metadata or text
        fb_headline, fb_author, fb_date = self._extract_fallback_metadata(html_text)
        if not headline:
            headline = fb_headline
        if not author:
            author = fb_author
        if not published_at:
            published_at = fb_date

        if not extracted_text or len(extracted_text.strip()) < 50:
            # Fallback text extraction from paragraph tags
            soup = bs4.BeautifulSoup(html_text, "lxml")
            p_tags = [p.get_text().strip() for p in soup.find_all("p")]
            valid_p = [p for p in p_tags if len(p) > 25]
            extracted_text = "\n\n".join(valid_p)

        clean_text = extracted_text.strip()
        if not clean_text:
            raise ValueError(f"Could not extract meaningful body text from {canonical_url}")

        raw_hash = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()
        article_id = ArticleRecord.generate_id(canonical_url)

        # 4. Paragraph Segmentation
        raw_paragraphs = [p.strip() for p in clean_text.splitlines() if p.strip()]
        paragraph_records: List[ArticleParagraphRecord] = []
        p_idx = 0
        for p in raw_paragraphs:
            p_clean = p.strip()
            # Filter out navigation noise or tiny footer disclaimers
            if len(p_clean) < 25:
                continue
            p_id = f"{article_id}_p{p_idx}"
            paragraph_records.append(
                ArticleParagraphRecord(
                    paragraph_id=p_id,
                    article_id=article_id,
                    paragraph_index=p_idx,
                    text=p_clean,
                    char_count=len(p_clean),
                )
            )
            p_idx += 1

        article_record = ArticleRecord(
            article_id=article_id,
            canonical_url=canonical_url,
            headline=headline or "Untitled Cricket Article",
            author=author,
            published_at_utc=published_at,
            source_domain=source_domain,
            full_text=clean_text,
            summary=clean_text[:250] + "..." if len(clean_text) > 250 else clean_text,
            language="en",
            raw_content_hash=raw_hash,
            provenance_id=prov.provenance_id,
        )

        return article_record, paragraph_records, prov

    def ingest(self, html_content: str | bytes, canonical_url: str, **kwargs: Any) -> Any:
        return self.parse_html(html_content, canonical_url, **kwargs)
