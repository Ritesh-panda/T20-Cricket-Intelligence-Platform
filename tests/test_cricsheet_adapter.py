"""Unit tests for Cricsheet Ingestion Adapter."""
from pathlib import Path
import pytest

from src.adapters.cricsheet_adapter import CricsheetAdapter


@pytest.fixture
def fixtures_dir():
    return Path(__file__).parent / "fixtures"


def test_parse_valid_cricsheet_fixture(fixtures_dir):
    adapter = CricsheetAdapter()
    sample_file = fixtures_dir / "cricsheet_sample_t20.json"
    result = adapter.parse_file(sample_file)

    # 1. Match checks
    assert result.match.match_id.startswith("cric_")
    assert result.match.tournament == "ICC Men's T20 World Cup"
    assert result.match.winner_id == "IND"
    assert result.match.win_by_runs == 7
    assert result.match.player_of_match_id == "player_v_kohli"

    # 2. Team & Player checks
    assert len(result.teams) == 2
    team_ids = {t.team_id for t in result.teams}
    assert "IND" in team_ids and "SOU" in team_ids

    # Players resolved with Cricsheet registry IDs
    kohli = next((p for p in result.players if p.player_id == "player_v_kohli"), None)
    assert kohli is not None
    assert kohli.cricsheet_id == "253802"

    # 3. Deliveries checks
    assert len(result.deliveries) > 0
    # Check phases
    pp_deliv = [d for d in result.deliveries if d.over == 0]
    assert all(d.phase.value == "powerplay" for d in pp_deliv)

    death_deliv = [d for d in result.deliveries if d.over == 19]
    assert all(d.phase.value == "death" for d in death_deliv)

    # 4. Score reconciliation
    assert result.reconciliation.match_id == result.match.match_id
    assert 1 in result.reconciliation.innings_totals
    assert 2 in result.reconciliation.innings_totals
    assert result.reconciliation.winner_reconciled is True

    # 5. Provenance audit
    assert result.provenance.source_name == "cricsheet"
    assert result.provenance.license_tag == "ODbL-1.0"
    assert len(result.provenance.content_hash_sha256) == 64


def test_parse_malformed_cricsheet_fixture(fixtures_dir):
    adapter = CricsheetAdapter()
    malformed_file = fixtures_dir / "cricsheet_malformed.json"
    with pytest.raises(ValueError, match="must contain at least 2 teams"):
        adapter.parse_file(malformed_file)
