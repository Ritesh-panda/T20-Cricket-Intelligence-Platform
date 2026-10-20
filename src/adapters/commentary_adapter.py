"""Commentary Ingestion & Parsing Adapter for T20 Cricket Intelligence Platform.

Adapts deterministic commentary grammar (ZainZoy) and Cricbuzz Next.js JSON extraction (HalcyonVector)
into a polite, validated adapter producing canonical CommentaryRecord entities.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.adapters.base import BaseSourceAdapter
from src.models.canonical import CommentaryRecord, SourceRecord

logger = logging.getLogger(__name__)

# Leading grammar: over.ball bowler to batter , description
LINE_GRAMMAR_RE = re.compile(
    r"^\s*(?P<over>\d+)\.(?P<ball>\d+):?\s+"
    r"(?P<bowler>.+?)\s+to\s+(?P<batter>.+?)\s*[,\-]\s*(?P<desc>.+?)\s*$",
    re.IGNORECASE,
)

# Header/structural lines to skip silently
SKIP_HEADER_RE = re.compile(
    r"^\s*(?:over\s+\d+|.*innings|toss\s*:|.*\bvs\.?\s|target\s*:|end\s+of\s+\w+)",
    re.IGNORECASE,
)

EVENT_PATTERNS = {
    "FOUR": re.compile(r"\b(?:four|4s?|boundary)\b", re.IGNORECASE),
    "SIX": re.compile(r"\b(?:six|6s?|maximum)\b", re.IGNORECASE),
    "WICKET": re.compile(r"\b(?:out|bowled|caught|lbw|run out|stumped|dismissed)\b", re.IGNORECASE),
    "DRS": re.compile(r"\b(?:drs|review|reviewed|ball tracking|ultraedge)\b", re.IGNORECASE),
    "FIFTY": re.compile(r"\b(?:fifty|half[- ]century|50\s+runs?)\b", re.IGNORECASE),
    "CENTURY": re.compile(r"\b(?:hundred|century|100\s+runs?)\b", re.IGNORECASE),
}


class CommentaryAdapter(BaseSourceAdapter):
    """Parses ball-by-ball text commentary into canonical CommentaryRecord objects."""

    def __init__(self, rate_limit_rps: float = 0.33, request_timeout_sec: int = 15):
        super().__init__(
            source_name="commentary_feed",
            rate_limit_rps=rate_limit_rps,
            request_timeout_sec=request_timeout_sec,
            user_agent="T20CricketResearchBot/1.0 (+https://example.org/t20-intel)",
        )

    def extract_event_tags(self, text: str) -> List[str]:
        """Extracts standardized milestone and outcome tags from commentary narrative."""
        tags = []
        for tag_name, pattern in EVENT_PATTERNS.items():
            if pattern.search(text):
                tags.append(tag_name)
        return tags

    def parse_raw_text(
        self,
        raw_text: str,
        match_id: str,
        innings: int = 1,
        source_domain: str = "cricbuzz.com",
    ) -> Tuple[List[CommentaryRecord], List[str]]:
        """Parses multi-line commentary text into CommentaryRecords. Returns (records, unparsed_lines)."""
        records: List[CommentaryRecord] = []
        unparsed_lines: List[str] = []
        now = datetime.now(timezone.utc)

        lines = raw_text.splitlines()
        for line_num, line in enumerate(lines, start=1):
            line_str = line.strip()
            if not line_str or SKIP_HEADER_RE.match(line_str):
                continue

            m = LINE_GRAMMAR_RE.match(line_str)
            if not m:
                unparsed_lines.append(f"Line {line_num}: {line_str}")
                continue

            over_num = int(m.group("over"))
            ball_num = int(m.group("ball"))
            bowler = m.group("bowler").strip()
            batter = m.group("batter").strip()
            desc = m.group("desc").strip()

            comm_id = f"comm_{match_id}_inn{innings}_ov{over_num}_b{ball_num}"
            tags = self.extract_event_tags(desc)

            record = CommentaryRecord(
                commentary_id=comm_id,
                match_id=match_id,
                innings=innings,
                over=over_num,
                ball=ball_num,
                bowler_raw=bowler,
                batter_raw=batter,
                text=desc,
                event_tags=tags,
                source_domain=source_domain,
                harvest_timestamp_utc=now,
            )
            records.append(record)

        return records, unparsed_lines

    def parse_cricbuzz_html_payload(
        self,
        html_bytes: bytes,
        match_id: str,
        source_url: str = "https://www.cricbuzz.com/live-cricket-scores/sample",
    ) -> Tuple[List[CommentaryRecord], SourceRecord]:
        """
        Extracts commentary from Cricbuzz Next.js inline streaming payload.
        Treats embedded JSON structure as fragile and gracefully falls back to DOM regex if modified.
        """
        prov = self.create_provenance_record(
            source_identifier=match_id,
            raw_bytes=html_bytes,
            source_url=source_url,
            license_tag="FairUse-ResearchExtraction",
            redistributable=False,
        )

        html_text = html_bytes.decode("utf-8", errors="replace")
        records: List[CommentaryRecord] = []

        # 1. Look for inline Next.js streaming chunks: self.__next_f.push([1, "..."])
        json_chunks = re.findall(r'self\.__next_f\.push\(\[\d+,\s*"(.*?)"\]\)', html_text)
        extracted_from_nextjs = False

        if json_chunks:
            for chunk in json_chunks:
                # Unescape escaped quotes/backslashes
                try:
                    clean_chunk = chunk.replace('\\"', '"').replace('\\\\', '\\')
                    # Look for commText and overNumber patterns
                    matches = re.finditer(
                        r'"overNumber":\s*(?P<ov>\d+)\.(?P<bl>\d+).*?"commText":\s*"(?P<txt>.*?)"',
                        clean_chunk,
                    )
                    for m in matches:
                        ov = int(m.group("ov"))
                        bl = int(m.group("bl"))
                        txt = m.group("txt")
                        comm_id = f"comm_{match_id}_inn1_ov{ov}_b{bl}"
                        records.append(
                            CommentaryRecord(
                                commentary_id=comm_id,
                                match_id=match_id,
                                innings=1,
                                over=ov,
                                ball=bl,
                                bowler_raw="Bowler",
                                batter_raw="Batter",
                                text=txt,
                                event_tags=self.extract_event_tags(txt),
                                source_domain="cricbuzz.com",
                                harvest_timestamp_utc=datetime.now(timezone.utc),
                                provenance_id=prov.provenance_id,
                            )
                        )
                        extracted_from_nextjs = True
                except Exception as e:
                    logger.debug(f"Next.js chunk parse error: {e}")

        # 2. Fallback: Parse line-by-line grammar if raw text is found in HTML body
        if not extracted_from_nextjs:
            clean_text_lines = re.findall(r"(\d+\.\d+\s+[^<]+to[^<]+,[^<]+)", html_text)
            if clean_text_lines:
                parsed_recs, _ = self.parse_raw_text(
                    "\n".join(clean_text_lines), match_id=match_id, source_domain="cricbuzz.com"
                )
                for r in parsed_recs:
                    # attach provenance
                    records.append(
                        CommentaryRecord(
                            commentary_id=r.commentary_id,
                            match_id=r.match_id,
                            innings=r.innings,
                            over=r.over,
                            ball=r.ball,
                            bowler_raw=r.bowler_raw,
                            batter_raw=r.batter_raw,
                            text=r.text,
                            event_tags=r.event_tags,
                            source_domain=r.source_domain,
                            harvest_timestamp_utc=r.harvest_timestamp_utc,
                            provenance_id=prov.provenance_id,
                        )
                    )

        return records, prov

    def ingest(self, raw_input: str | bytes, match_id: str, **kwargs: Any) -> Any:
        if isinstance(raw_input, bytes):
            return self.parse_cricbuzz_html_payload(raw_input, match_id=match_id)
        return self.parse_raw_text(raw_input, match_id=match_id)
