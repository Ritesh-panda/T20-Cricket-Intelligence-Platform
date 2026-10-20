"""Unit tests for canonical Pydantic schemas."""
import pytest
from datetime import datetime, timezone

from src.models.canonical import (
    DeliveryRecord,
    MatchPhase,
    MatchRecord,
    PlayerRecord,
    SourceRecord,
    TeamRecord,
    ArticleRecord,
    EventAlignmentRecord,
    WicketKind,
)


def test_team_record_validation():
    team = TeamRecord(team_id="ind ", name="India", aliases=["IND", "Team India"])
    assert team.team_id == "IND"

    with pytest.raises(ValueError):
        TeamRecord(team_id="  ", name="Blank")


def test_player_record_creation():
    player = PlayerRecord(
        player_id="player_virat_kohli",
        full_name="Virat Kohli",
        cricsheet_id="253802",
        primary_team_id="IND",
        batting_style="Right-hand bat",
        aliases=["Kohli", "King Kohli"],
    )
    assert player.player_id == "player_virat_kohli"
    assert player.primary_team_id == "IND"


def test_delivery_record_validation():
    # Valid delivery
    deliv = DeliveryRecord(
        delivery_id="del_match1_inn1_ov0_b1",
        match_id="match1",
        innings=1,
        over=0,
        ball=1,
        batter_id="player_rohit",
        bowler_id="player_starc",
        batter_runs=4,
        extra_runs=0,
        total_runs=4,
        is_legal=True,
        is_wicket=False,
        phase=MatchPhase.POWERPLAY,
    )
    assert deliv.total_runs == 4

    # Invalid: total runs does not match sum
    with pytest.raises(ValueError, match="total_runs"):
        DeliveryRecord(
            delivery_id="del_match1_inn1_ov0_b2",
            match_id="match1",
            innings=1,
            over=0,
            ball=2,
            batter_id="player_rohit",
            bowler_id="player_starc",
            batter_runs=4,
            extra_runs=0,
            total_runs=6,  # Mismatch!
            is_legal=True,
            is_wicket=False,
            phase=MatchPhase.POWERPLAY,
        )

    # Invalid: wicket without player_dismissed_id
    with pytest.raises(ValueError, match="player_dismissed_id"):
        DeliveryRecord(
            delivery_id="del_match1_inn1_ov0_b3",
            match_id="match1",
            innings=1,
            over=0,
            ball=3,
            batter_id="player_rohit",
            bowler_id="player_starc",
            batter_runs=0,
            extra_runs=0,
            total_runs=0,
            is_legal=True,
            is_wicket=True,
            wicket_kind="bowled",
            player_dismissed_id=None,  # Missing!
            phase=MatchPhase.POWERPLAY,
        )


def test_source_record_sha256():
    # Valid 64-char hex
    valid_hash = "a" * 64
    sr = SourceRecord(
        provenance_id="prov_test",
        source_name="cricsheet",
        source_identifier="1411166.json",
        harvest_timestamp_utc=datetime.now(timezone.utc),
        content_hash_sha256=valid_hash,
        license_tag="ODbL-1.0",
        redistributable=True,
    )
    assert sr.content_hash_sha256 == valid_hash

    # Invalid hash length
    with pytest.raises(ValueError, match="64-character hex"):
        SourceRecord(
            provenance_id="prov_test",
            source_name="cricsheet",
            source_identifier="1411166.json",
            harvest_timestamp_utc=datetime.now(timezone.utc),
            content_hash_sha256="short_hash",
            license_tag="ODbL-1.0",
        )


def test_article_record_id_generation():
    url = "https://www.espncricinfo.com/story/t20-world-cup-final-ind-vs-sa-1411166"
    art_id = ArticleRecord.generate_id(url)
    assert art_id.startswith("art_")
    assert len(art_id) == 20  # "art_" + 16 hex chars
