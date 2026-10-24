"""Pydantic Models for News Articles, Paragraphs, and Ball-by-Ball Commentary."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ArticleResponse(BaseModel):
    """News article summary record without large full-text payload."""
    article_id: str
    canonical_url: str
    headline: str
    author: Optional[str] = None
    published_at_utc: Optional[str] = None
    source_domain: str
    summary: Optional[str] = None
    language: str
    raw_content_hash: str
    provenance_id: Optional[str] = None


class ArticleDetailResponse(ArticleResponse):
    """Full article record including body text."""
    full_text: str


class ArticleParagraphResponse(BaseModel):
    """Discrete paragraph segment for fine-grained NLP and event alignment."""
    paragraph_id: str
    article_id: str
    paragraph_index: int
    text: str
    char_count: int


class CommentaryResponse(BaseModel):
    """Ball-by-ball written commentary entry."""
    commentary_id: str
    match_id: str
    innings: int
    over_num: int
    ball_num: int
    bowler_raw: str
    batter_raw: str
    text: str
    event_tags: List[str] = Field(default_factory=list)
    source_domain: str
    harvest_timestamp_utc: str
    provenance_id: Optional[str] = None
