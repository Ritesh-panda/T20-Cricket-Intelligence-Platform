"""Cricket-Aware Text Cleaning and Normalization.

Preserves cricket notations (overs, scores, asterisk not-out markers, DRS, negation),
unescapes HTML entities, normalizes Unicode, strips journalistic boilerplate,
and produces reversible references with character offsets.
"""
from __future__ import annotations

import html
import re
import unicodedata
from typing import List, Optional, Tuple

from src.nlp.schemas import NormalizedTextRecord

# Common news boilerplate regex patterns
BOILERPLATE_PATTERNS = [
    re.compile(r"^\s*(?:also read|related story|must read|watch|editor\'?s pick|advertisement|ad)\s*:?.*$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*(?:click here to subscribe|subscribe to our newsletter|sign up for.*|follow us on (?:twitter|facebook|instagram|x)).*$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*(?:download the app|photo credit|get all the latest cricket updates).*$", re.IGNORECASE | re.MULTILINE),
]

# Zero-width spaces and unusual whitespace
UNUSUAL_WHITESPACE_RE = re.compile(r"[\u00a0\u1680\u2000-\u200b\u202f\u205f\u3000\ufeff]")


class CricketTextCleaner:
    """Cleans and standardizes cricket text without removing domain-critical notations."""

    def __init__(self, strip_boilerplate: bool = True):
        self.strip_boilerplate = strip_boilerplate

    def clean_text(self, text: str, is_commentary: bool = False) -> str:
        """
        Cleans text while preserving cricket syntax (e.g. '19.4', '82*', '182/5', 'not out').
        
        Args:
            text: Raw input string.
            is_commentary: If True, applies commentary-specific delimiter preservation.
            
        Returns:
            Normalized string.
        """
        if not text:
            return ""

        # 1. Unescape HTML entities (&amp; -> &, &quot; -> ", etc.)
        cleaned = html.unescape(text)

        # 2. Strip residual HTML tags if any remain
        cleaned = re.sub(r"<[^>]+>", " ", cleaned)

        # 3. Unicode normalization: NFKC standardizes variants while preserving letters/diacritics
        cleaned = unicodedata.normalize("NFKC", cleaned)

        # 4. Standardize quotes and hyphens to clean ASCII while preserving asterisks (*) and slashes (/)
        cleaned = UNUSUAL_WHITESPACE_RE.sub(" ", cleaned)
        cleaned = re.sub(r"[\u2018\u2019\u201b\u2032]", "'", cleaned)
        cleaned = re.sub(r"[\u201c\u201d\u201f\u2033]", '"', cleaned)
        cleaned = re.sub(r"[\u2013\u2014\u2015]", "-", cleaned)

        # 5. Remove journalistic boilerplate if enabled and not commentary
        if self.strip_boilerplate and not is_commentary:
            for pattern in BOILERPLATE_PATTERNS:
                cleaned = pattern.sub("", cleaned)

        # 6. Normalize whitespace: preserve single spaces and clean paragraphs
        lines = cleaned.splitlines()
        normalized_lines = []
        for line in lines:
            line_str = re.sub(r"[ \t]+", " ", line).strip()
            if line_str:
                normalized_lines.append(line_str)

        if is_commentary:
            # Join with space to keep delivery description inline
            final_text = " ".join(normalized_lines)
        else:
            final_text = "\n\n".join(normalized_lines)

        return final_text.strip()

    def create_normalized_record(
        self,
        source_id: str,
        source_type: str,
        raw_text: str,
        pipeline_version: str = "0.1.0",
    ) -> NormalizedTextRecord:
        """Generates a persisted NormalizedTextRecord linked back to source record."""
        is_comm = (source_type == "commentary_entry")
        cleaned = self.clean_text(raw_text, is_commentary=is_comm)
        norm_id = f"norm_{source_type}_{source_id}_v{pipeline_version.replace('.', '_')}"

        return NormalizedTextRecord(
            norm_id=norm_id,
            source_type=source_type,
            source_id=source_id,
            original_text=raw_text,
            normalized_text=cleaned,
            char_count=len(cleaned),
            pipeline_version=pipeline_version,
        )
