"""API Routes for News Articles and Paragraphs."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from fastapi import APIRouter, Depends, Query

from src.api.dependencies import get_storage, pagination_params
from src.api.errors import ResourceNotFoundError
from src.api.schemas.common import PaginatedResponse
from src.api.schemas.editorial import (
    ArticleDetailResponse,
    ArticleParagraphResponse,
    ArticleResponse,
)
from src.storage.sqlite_manager import SQLiteStorageManager

router = APIRouter(prefix="/articles", tags=["Articles & Editorial Commentary"])


def _parse_article_summary(row: Any) -> ArticleResponse:
    return ArticleResponse(
        article_id=row["article_id"],
        canonical_url=row["canonical_url"],
        headline=row["headline"],
        author=row["author"],
        published_at_utc=row["published_at_utc"],
        source_domain=row["source_domain"],
        summary=row["summary"],
        language=row["language"],
        raw_content_hash=row["raw_content_hash"],
        provenance_id=row["provenance_id"],
    )


def _parse_article_detail(row: Any) -> ArticleDetailResponse:
    return ArticleDetailResponse(
        article_id=row["article_id"],
        canonical_url=row["canonical_url"],
        headline=row["headline"],
        author=row["author"],
        published_at_utc=row["published_at_utc"],
        source_domain=row["source_domain"],
        summary=row["summary"],
        language=row["language"],
        raw_content_hash=row["raw_content_hash"],
        provenance_id=row["provenance_id"],
        full_text=row["full_text"],
    )


def _parse_paragraph(row: Any) -> ArticleParagraphResponse:
    return ArticleParagraphResponse(
        paragraph_id=row["paragraph_id"],
        article_id=row["article_id"],
        paragraph_index=int(row["paragraph_index"]),
        text=row["text"],
        char_count=int(row["char_count"]),
    )


@router.get("", response_model=PaginatedResponse[ArticleResponse])
def list_articles(
    source_domain: Optional[str] = Query(None, description="Filter by publisher domain"),
    language: Optional[str] = Query(None, description="Filter by language code (e.g. en)"),
    pagination: Tuple[int, int] = Depends(pagination_params),
    storage: SQLiteStorageManager = Depends(get_storage),
) -> PaginatedResponse[ArticleResponse]:
    """Retrieves paginated news article metadata with safe publisher/language filtering."""
    limit, offset = pagination
    where_clauses: List[str] = []
    params: List[Any] = []

    if source_domain:
        where_clauses.append("source_domain = ?")
        params.append(source_domain.strip().lower())
    if language:
        where_clauses.append("language = ?")
        params.append(language.strip().lower())

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    with storage._get_connection() as conn:
        count_query = f"SELECT COUNT(*) FROM articles {where_sql};"
        total = conn.execute(count_query, params).fetchone()[0]

        query = f"""
            SELECT article_id, canonical_url, headline, author, published_at_utc,
                   source_domain, summary, language, raw_content_hash, provenance_id
            FROM articles
            {where_sql}
            ORDER BY published_at_utc DESC NULLS LAST, article_id DESC
            LIMIT ? OFFSET ?;
        """
        rows = conn.execute(query, params + [limit, offset]).fetchall()
        items = [_parse_article_summary(r) for r in rows]

    return PaginatedResponse.create(items=items, total=total, limit=limit, offset=offset)


@router.get("/{article_id}", response_model=ArticleDetailResponse)
def get_article(
    article_id: str,
    storage: SQLiteStorageManager = Depends(get_storage),
) -> ArticleDetailResponse:
    """Retrieves complete article including full text and provenance attribution or returns 404."""
    with storage._get_connection() as conn:
        row = conn.execute("SELECT * FROM articles WHERE article_id = ?;", (article_id,)).fetchone()
        if not row:
            raise ResourceNotFoundError("articles", article_id)
        return _parse_article_detail(row)


@router.get("/{article_id}/paragraphs", response_model=PaginatedResponse[ArticleParagraphResponse])
def get_article_paragraphs(
    article_id: str,
    pagination: Tuple[int, int] = Depends(pagination_params),
    storage: SQLiteStorageManager = Depends(get_storage),
) -> PaginatedResponse[ArticleParagraphResponse]:
    """Retrieves ordered paragraph segments for a specific article."""
    limit, offset = pagination

    with storage._get_connection() as conn:
        # Check article existence first
        art_exists = conn.execute(
            "SELECT 1 FROM articles WHERE article_id = ?;", (article_id,)
        ).fetchone()
        if not art_exists:
            raise ResourceNotFoundError("articles", article_id)

        count_query = "SELECT COUNT(*) FROM article_paragraphs WHERE article_id = ?;"
        total = conn.execute(count_query, (article_id,)).fetchone()[0]

        query = """
            SELECT * FROM article_paragraphs
            WHERE article_id = ?
            ORDER BY paragraph_index ASC
            LIMIT ? OFFSET ?;
        """
        rows = conn.execute(query, (article_id, limit, offset)).fetchall()
        items = [_parse_paragraph(r) for r in rows]

    return PaginatedResponse.create(items=items, total=total, limit=limit, offset=offset)
