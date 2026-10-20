"""Unit tests for Commentary Ingestion & Parsing Adapter."""
from pathlib import Path
import pytest

from src.adapters.commentary_adapter import CommentaryAdapter


@pytest.fixture
def fixtures_dir():
    return Path(__file__).parent / "fixtures"


def test_parse_commentary_text_lines(fixtures_dir):
    adapter = CommentaryAdapter()
    text_file = fixtures_dir / "sample_commentary.txt"
    with open(text_file, "r", encoding="utf-8") as f:
        content = f.read()

    records, unparsed = adapter.parse_raw_text(
        raw_text=content,
        match_id="t20wc_final_2024",
        innings=1,
        source_domain="cricbuzz.com",
    )

    assert len(records) > 10
    assert len(unparsed) == 0

    first = records[0]
    assert first.over == 0
    assert first.ball == 1
    assert first.bowler_raw == "Jansen"
    assert first.batter_raw == "Rohit"
    assert "FOUR" in first.event_tags

    # Check wicket detection in over 19
    wkt_record = next(r for r in records if r.over == 19 and r.ball == 1)
    assert "WICKET" in wkt_record.event_tags
    assert wkt_record.bowler_raw == "Pandya"
    assert wkt_record.batter_raw == "Miller"


def test_cricbuzz_nextjs_payload_parsing():
    adapter = CommentaryAdapter()
    # Mock Next.js streaming HTML with inline chunk
    sample_html = b"""
    <html>
      <head><title>Live Match</title></head>
      <body>
        <script>
          self.__next_f.push([1, "{\\"overNumber\\": 15.3, \\"commText\\": \\"FOUR, cracked through the covers in style!\\"}"]);
        </script>
      </body>
    </html>
    """
    records, prov = adapter.parse_cricbuzz_html_payload(sample_html, match_id="mock_match_01")
    assert len(records) == 1
    rec = records[0]
    assert rec.over == 15
    assert rec.ball == 3
    assert "FOUR" in rec.event_tags
    assert prov.provenance_id.startswith("prov_")
