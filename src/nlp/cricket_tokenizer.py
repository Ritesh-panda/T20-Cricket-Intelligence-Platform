"""Cricket-Aware Tokenizer for T20 Cricket Intelligence.

Tokenizes text while preserving cricket compound terms, over notation (19.4),
score strings (182/5, 45-2), asterisk not-out scores (82*), acronyms, and player initials.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class TokenizationMode(str, Enum):
    EDITORIAL = "editorial"
    COMMENTARY = "commentary"


@dataclass(frozen=True)
class CricketToken:
    """Represents a token with text, character offsets, and semantic tag."""
    text: str
    start_char: int
    end_char: int
    token_type: str  # OVER, SCORE, ACRONYM, COMPOUND_TERM, WORD, NUMBER, PUNCT


# Pre-compiled regex patterns for cricket syntax
RE_OVER = re.compile(r"^\d{1,2}\.[1-6]$")
RE_SCORE = re.compile(r"^\d{1,3}[/-]\d{1,2}(?:\*|(?:\s*all\s*out))?$", re.IGNORECASE)
RE_RUNS_ASTERISK = re.compile(r"^\d{1,3}\*$")

CRICKET_ACRONYMS = {
    "T20", "T20I", "ODI", "TEST", "DRS", "LBW", "DLS", "RR", "RPO",
    "ECO", "SR", "C&B", "MOM", "MOS", "ICC", "BCCI", "PCB", "ECB",
    "CA", "CSA", "NZC", "WICB", "IPL", "BBL", "PSL", "CPL",
}

CRICKET_COMPOUNDS = [
    "run out", "not out", "retired hurt", "retired out", "timed out",
    "powerplay", "death overs", "middle overs", "dot ball", "free hit",
    "no ball", "wide ball", "leg bye", "caught behind", "hat-trick",
    "hat trick", "super over", "maiden over", "caught and bowled",
    "fall of wickets", "man of the match", "player of the match",
]


class CricketTokenizer:
    """Deterministic cricket tokenizer with span tracking and domain-specific rules."""

    def __init__(self, mode: TokenizationMode = TokenizationMode.EDITORIAL):
        self.mode = mode
        # Build compound regex: longest match first
        sorted_compounds = sorted(CRICKET_COMPOUNDS, key=len, reverse=True)
        compound_pattern = r"|".join(rf"\b{re.escape(c)}\b" for c in sorted_compounds)
        self._compound_re = re.compile(rf"({compound_pattern})", re.IGNORECASE)

        # Token specification regex
        # 1. Over notation: e.g. 19.4 or 0.1
        # 2. Score notation: e.g. 182/5, 45-2, 82*
        # 3. Words with hyphens/apostrophes (e.g. Kohli's, caught-and-bowled)
        # 4. Numbers
        # 5. Punctuation
        self._token_pattern = re.compile(
            r"(?P<OVER>\b\d{1,2}\.[1-6]\b)"
            r"|(?P<SCORE>\b\d{1,3}[/-]\d{1,2}\*?(?!\w)|\b\d{1,3}\*(?!\w))"
            r"|(?P<ACRONYM>\b(?:T20I?|ODI|TEST|DRS|LBW|DLS|RPO|BCCI|PCB|ECB|IPL|BBL|PSL|CPL)\b)"
            r"|(?P<WORD>[A-Za-z]+(?:['’\-][A-Za-z]+)*)"
            r"|(?P<NUMBER>\b\d+\b)"
            r"|(?P<PUNCT>[^\w\s])",
            re.UNICODE,
        )

    def tokenize(self, text: str) -> List[CricketToken]:
        """
        Tokenizes text into CricketToken instances with character offsets.
        Preserves multi-word compound terms before single-word decomposition.
        """
        if not text:
            return []

        tokens: List[CricketToken] = []
        # Step 1: Detect multi-word compounds and track their character spans
        compound_spans: List[tuple[int, int, str]] = []
        for m in self._compound_re.finditer(text):
            compound_spans.append((m.start(), m.end(), m.group(0)))

        # Step 2: Iterate through token pattern, skipping spans covered by compounds
        pos = 0
        compound_idx = 0
        total_compounds = len(compound_spans)

        for match in self._token_pattern.finditer(text):
            m_start, m_end = match.start(), match.end()

            # Check if this match falls inside an active compound
            while compound_idx < total_compounds and compound_spans[compound_idx][1] <= m_start:
                compound_idx += 1

            if compound_idx < total_compounds:
                c_start, c_end, c_text = compound_spans[compound_idx]
                if c_start <= m_start < c_end:
                    # If this is the start of the compound, emit the compound token
                    if m_start == c_start or not any(t.start_char == c_start for t in tokens):
                        tokens.append(
                            CricketToken(
                                text=c_text,
                                start_char=c_start,
                                end_char=c_end,
                                token_type="COMPOUND_TERM",
                            )
                        )
                    continue

            # Standard token classification
            val = match.group(0)
            kind = match.lastgroup or "WORD"

            if kind == "OVER":
                token_type = "CRICKET_OVER"
            elif kind == "SCORE":
                token_type = "CRICKET_SCORE"
            elif kind == "ACRONYM":
                token_type = "CRICKET_ACRONYM"
            elif kind == "WORD":
                val_upper = val.upper()
                if val_upper in CRICKET_ACRONYMS:
                    token_type = "CRICKET_ACRONYM"
                elif RE_OVER.match(val):
                    token_type = "CRICKET_OVER"
                elif RE_SCORE.match(val) or RE_RUNS_ASTERISK.match(val):
                    token_type = "CRICKET_SCORE"
                else:
                    token_type = "WORD"
            elif kind == "NUMBER":
                token_type = "NUMBER"
            else:
                token_type = "PUNCT"

            tokens.append(
                CricketToken(
                    text=val,
                    start_char=m_start,
                    end_char=m_end,
                    token_type=token_type,
                )
            )

        return tokens
