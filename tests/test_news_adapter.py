"""Unit tests for News Article Ingestion Adapter."""
from pathlib import Path
import pytest

from src.adapters.news_adapter import NewsArticleAdapter


@pytest.fixture
def fixtures_dir():
    return Path(__file__).parent / "fixtures"


def test_parse_sample_news_article(fixtures_dir):
    adapter = NewsArticleAdapter()
    article_file = fixtures_dir / "sample_article.html"
    with open(article_file, "r", encoding="utf-8") as f:
        html_text = f.read()

    url = "https://www.wisden.com/matches/reports/t20-world-cup-final-india-south-africa"
    article, paragraphs, prov = adapter.parse_html(
        html_content=html_text,
        canonical_url=url,
        source_domain="wisden.com",
    )

    # 1. Headline & metadata
    assert "India Clinch T20 World Cup" in article.headline
    assert article.author == "Feroz Khan"
    assert article.published_at_utc is not None
    assert article.source_domain == "wisden.com"
    assert article.article_id.startswith("art_")

    # 2. Paragraph segmentation
    assert len(paragraphs) >= 4
    for idx, p in enumerate(paragraphs):
        assert p.paragraph_index == idx
        assert p.article_id == article.article_id
        assert p.char_count == len(p.text)
        assert len(p.text) > 25

    # 3. Provenance
    assert prov.source_name == "publisher_news"
    assert prov.license_tag == "FairUse-ResearchExtraction"
    assert prov.redistributable is False
