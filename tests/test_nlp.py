"""Comprehensive Unit & Integration Test Suite for Phase 4 NLP Layer.

Tests:
1. Cricket-aware text cleaning & notation preservation.
2. Tokenization of overs, scores, asterisks, compounds, and acronyms.
3. Gazetteer boundary matching and alias disambiguation.
4. Named Entity Recognition span offsets and overlap resolution.
5. Multi-signal Entity Resolution (contextual team boost, ambiguity gating).
6. Sentiment baselines (general sentiment, negation, event polarity, bowler vs batter framing).
7. End-to-end pipeline idempotency and transactional rollback.
8. Evaluation metrics calculation.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List
import pytest

from src.models.canonical import ArticleParagraphRecord, ArticleRecord
from src.nlp.cricket_tokenizer import CricketTokenizer, TokenizationMode
from src.nlp.entity_resolver import EntityResolver
from src.nlp.evaluation import (
    compute_ner_metrics,
    compute_resolution_metrics,
    compute_sentiment_metrics,
)
from src.nlp.gazetteer import CricketGazetteer
from src.nlp.ner import CricketNER
from src.nlp.processing_pipeline import NLPPipeline
from src.nlp.schemas import EntityType, ResolutionStatus, SentimentLabel
from src.nlp.sentiment import CricketSentimentBaseline
from src.nlp.text_cleaner import CricketTextCleaner
from src.storage.sqlite_manager import SQLiteStorageManager


@pytest.fixture
def temp_db(tmp_path: Path) -> SQLiteStorageManager:
    db_file = tmp_path / "test_nlp.db"
    return SQLiteStorageManager(db_file)


@pytest.fixture
def gazetteer(temp_db: SQLiteStorageManager) -> CricketGazetteer:
    # Uses seed yaml and empty db sync
    return CricketGazetteer(storage=temp_db)


# -----------------------------------------------------------------------------
# 1. Text Cleaning & Notation Preservation Tests
# -----------------------------------------------------------------------------
def test_text_cleaning_preserves_mandatory_cricket_examples():
    cleaner = CricketTextCleaner()

    examples = [
        "19.4 Bumrah to Kohli, SIX!",
        "India need 12 runs from 6 balls.",
        "Kohli scored 82* from 53 balls.",
        "The decision was overturned after DRS.",
        "India did not qualify for the final.",
    ]

    for ex in examples:
        cleaned = cleaner.clean_text(ex)
        # Verify exact critical terms and notations are preserved intact
        assert ex == cleaned, f"Expected '{ex}', got '{cleaned}'"


def test_text_cleaning_unescapes_html_and_normalizes_unicode():
    cleaner = CricketTextCleaner()
    raw = "India &amp; South Africa played a &ldquo;thriller&rdquo;&nbsp;in Bridgetown."
    cleaned = cleaner.clean_text(raw)
    assert cleaned == 'India & South Africa played a "thriller" in Bridgetown.'


def test_text_cleaning_strips_boilerplate():
    cleaner = CricketTextCleaner(strip_boilerplate=True)
    raw = (
        "Rohit Sharma praised the bowling effort in Barbados.\n\n"
        "Also Read: Full match scorecard and player ratings\n\n"
        "Click here to subscribe to our newsletter for more updates."
    )
    cleaned = cleaner.clean_text(raw)
    assert "Rohit Sharma praised the bowling effort in Barbados." in cleaned
    assert "Also Read" not in cleaned
    assert "subscribe" not in cleaned


# -----------------------------------------------------------------------------
# 2. Cricket-Aware Tokenization Tests
# -----------------------------------------------------------------------------
def test_tokenizer_cricket_overs_scores_and_compounds():
    tokenizer = CricketTokenizer(mode=TokenizationMode.EDITORIAL)
    text = "In over 19.4, India reached 182/5 as Kohli stayed 82* not out during the death overs."

    tokens = tokenizer.tokenize(text)
    token_texts = [t.text for t in tokens]
    token_types = {t.text: t.token_type for t in tokens}

    # Verify cricket overs and scores
    assert "19.4" in token_texts
    assert token_types["19.4"] == "CRICKET_OVER"

    assert "182/5" in token_texts
    assert token_types["182/5"] == "CRICKET_SCORE"

    assert "82*" in token_texts
    assert token_types["82*"] == "CRICKET_SCORE"

    # Verify compound terms
    assert "not out" in token_texts
    assert token_types["not out"] == "COMPOUND_TERM"

    assert "death overs" in token_texts
    assert token_types["death overs"] == "COMPOUND_TERM"


def test_tokenizer_acronyms_and_boundaries():
    tokenizer = CricketTokenizer()
    text = "Review taken under DRS after an appeal for LBW in T20I match."
    tokens = tokenizer.tokenize(text)
    token_types = {t.text: t.token_type for t in tokens}

    assert token_types["DRS"] == "CRICKET_ACRONYM"
    assert token_types["LBW"] == "CRICKET_ACRONYM"
    assert token_types["T20I"] == "CRICKET_ACRONYM"


# -----------------------------------------------------------------------------
# 3. Gazetteer & Boundary Matching Tests
# -----------------------------------------------------------------------------
def test_gazetteer_boundary_matching_prevents_substring_false_positives(gazetteer: CricketGazetteer):
    # 'In' should not match India, 'SA' should not match USA
    text = "In the USA, cricket is growing rapidly while South Africa trains in Barbados."
    matches = gazetteer.find_matches(text)

    matched_surfaces = [m[2] for m in matches]
    # Should match South Africa and Barbados
    assert "South Africa" in matched_surfaces
    assert "Barbados" in matched_surfaces
    # Should NOT match 'In' or 'SA' inside USA
    assert "In" not in matched_surfaces
    assert "SA" not in matched_surfaces


def test_gazetteer_longest_phrase_priority(gazetteer: CricketGazetteer):
    text = "West Indies announced their squad for the ICC Men's T20 World Cup."
    matches = gazetteer.find_matches(text)
    matched_surfaces = [m[2] for m in matches]

    # Full phrase matches should be prioritized
    assert "West Indies" in matched_surfaces
    assert "ICC Men's T20 World Cup" in matched_surfaces


# -----------------------------------------------------------------------------
# 4. Named Entity Recognition Tests
# -----------------------------------------------------------------------------
def test_ner_exact_character_offsets(gazetteer: CricketGazetteer):
    ner = CricketNER(gazetteer=gazetteer)
    text = "Virat Kohli and Jasprit Bumrah led India to victory."

    mentions = ner.extract_mentions(text, source_id="p0")
    assert len(mentions) == 3

    # Check first mention: Virat Kohli
    m0 = mentions[0]
    assert m0.surface_text == "Virat Kohli"
    assert text[m0.start_char : m0.end_char] == "Virat Kohli"
    assert m0.entity_type == EntityType.PLAYER

    # Check third mention: India
    m2 = mentions[2]
    assert m2.surface_text == "India"
    assert text[m2.start_char : m2.end_char] == "India"
    assert m2.entity_type == EntityType.TEAM


def test_ner_overlapping_spans_prefers_longer(gazetteer: CricketGazetteer):
    ner = CricketNER(gazetteer=gazetteer)
    text = "Captain Virat Kohli played a steady knock."
    mentions = ner.extract_mentions(text, source_id="p0")

    # Should detect "Virat Kohli", not duplicate "Kohli"
    surfaces = [m.surface_text for m in mentions]
    assert "Virat Kohli" in surfaces
    assert surfaces.count("Kohli") == 0


# -----------------------------------------------------------------------------
# 5. Entity Resolution Tests (Contextual Signals)
# -----------------------------------------------------------------------------
def test_entity_resolution_unambiguous_player(gazetteer: CricketGazetteer):
    ner = CricketNER(gazetteer=gazetteer)
    resolver = EntityResolver(gazetteer=gazetteer)

    text = "King Kohli delivered once again in Barbados."
    mentions = ner.extract_mentions(text, source_id="p0")
    resolved_mentions, audits = resolver.resolve_mentions(mentions, document_text=text)

    kohli_m = [m for m in resolved_mentions if m.surface_text == "King Kohli"][0]
    assert kohli_m.resolution_status == ResolutionStatus.RESOLVED
    assert kohli_m.resolved_id == "player_virat_kohli"
    assert kohli_m.confidence >= 0.90


def test_entity_resolution_ambiguous_surname_without_context(gazetteer: CricketGazetteer):
    ner = CricketNER(gazetteer=gazetteer)
    resolver = EntityResolver(gazetteer=gazetteer)

    # Isolated ambiguous surname "Pandya" without team mention
    text = "Pandya struck a boundary through extra cover."
    mentions = ner.extract_mentions(text, source_id="p0")
    resolved_mentions, audits = resolver.resolve_mentions(mentions, document_text=text)

    pandya_m = [m for m in resolved_mentions if m.surface_text == "Pandya"][0]
    # Without context, score is below threshold -> UNRESOLVED / AMBIGUOUS
    assert pandya_m.resolution_status in (ResolutionStatus.AMBIGUOUS, ResolutionStatus.UNRESOLVED)
    assert pandya_m.resolved_id is None


def test_entity_resolution_ambiguous_surname_with_team_context(gazetteer: CricketGazetteer):
    ner = CricketNER(gazetteer=gazetteer)
    resolver = EntityResolver(gazetteer=gazetteer)

    # Context includes "India", so Pandya gets +0.30 team boost to resolve to Hardik Pandya!
    text = "India needed quick runs as Pandya walked out to bat."
    mentions = ner.extract_mentions(text, source_id="p0")
    resolved_mentions, audits = resolver.resolve_mentions(mentions, document_text=text)

    pandya_m = [m for m in resolved_mentions if m.surface_text == "Pandya"][0]
    assert pandya_m.resolution_status == ResolutionStatus.RESOLVED
    assert pandya_m.resolved_id == "player_hardik_pandya"
    assert pandya_m.confidence >= 0.65


# -----------------------------------------------------------------------------
# 6. Sentiment & Framing Baselines Tests
# -----------------------------------------------------------------------------
def test_sentiment_negation_handling():
    engine = CricketSentimentBaseline()

    # Affirmative positive
    res_pos = engine.score_text("India achieved a brilliant and magnificent triumph.", source_id="s1")
    assert res_pos.general_sentiment == SentimentLabel.POSITIVE
    assert res_pos.compound_score > 0.3

    # Negated positive
    res_neg = engine.score_text("India did not achieve a brilliant victory and suffered disaster.", source_id="s2")
    assert res_neg.general_sentiment == SentimentLabel.NEGATIVE
    assert res_neg.compound_score < -0.2


def test_sentiment_bowler_vs_batter_framing():
    engine = CricketSentimentBaseline()
    text = "Bumrah struck with a searing yorker, taking the wicket as the batter was bowled."

    # For bowler (Bumrah) -> Wickets are POSITIVE framing!
    bowler_sent = engine.score_text(text, source_id="s1", target_entity_id="player_jasprit_bumrah", is_bowling_context=True)
    assert bowler_sent.framing_score > 0.0

    # For batting team -> Wicket is ADVERSE framing!
    batter_sent = engine.score_text(text, source_id="s1", target_entity_id="team_batting", is_bowling_context=False)
    assert batter_sent.framing_score < 0.0


# -----------------------------------------------------------------------------
# 7. End-to-End Pipeline & Idempotency Tests
# -----------------------------------------------------------------------------
def test_nlp_pipeline_idempotent_processing(temp_db: SQLiteStorageManager):
    # Setup test article and paragraph in SQLite
    article = ArticleRecord(
        article_id="art_nlp_001",
        canonical_url="https://www.espncricinfo.com/story/nlp-test",
        headline="Kohli stars as India defeat South Africa",
        source_domain="espncricinfo.com",
        full_text="Virat Kohli scored 76 runs as India edged South Africa in the T20 World Cup final.",
        summary="India win.",
        raw_content_hash="11112222" + "0" * 56,
    )
    paragraphs = [
        ArticleParagraphRecord(
            paragraph_id="art_nlp_001_p0",
            article_id="art_nlp_001",
            paragraph_index=0,
            text=article.full_text,
            char_count=len(article.full_text),
        )
    ]
    temp_db.insert_article_with_paragraphs(article, paragraphs)

    pipeline = NLPPipeline(storage=temp_db)

    # First run
    metrics1 = pipeline.process_records(process_all=True)
    assert metrics1.records_processed == 1
    assert metrics1.mentions_extracted >= 3
    assert temp_db.get_nlp_metrics()["normalized_texts_count"] == 1

    # Second run on unchanged data -> Idempotent upsert, count unchanged
    metrics2 = pipeline.process_records(process_all=True)
    assert metrics2.records_processed == 1
    assert temp_db.get_nlp_metrics()["normalized_texts_count"] == 1


def test_nlp_transaction_rollback_on_failure(temp_db: SQLiteStorageManager):
    """Verifies that an error during mention persistence rolls back cleanly."""
    from src.nlp.schemas import EntityMentionRecord

    # Valid mention
    m1 = EntityMentionRecord(
        mention_id="men_rb_01",
        source_type="article_paragraph",
        source_id="p0",
        entity_type=EntityType.PLAYER,
        surface_text="Kohli",
        start_char=0,
        end_char=5,
        confidence=0.9,
    )
    temp_db.upsert_entity_mentions([m1])

    # Attempt a batch that violates non-null constraint inside transaction
    try:
        with temp_db._get_connection() as conn:
            conn.execute("INSERT INTO entity_mentions (mention_id, source_type, source_id, entity_type, surface_text, start_char, end_char, detection_method, confidence, resolution_status, pipeline_version, created_at_utc) VALUES ('men_rb_02', 'p', 's', 'PLAYER', 'Bumrah', 0, 6, 'm', 0.9, 'RESOLVED', '1.0', 'now')")
            # Force syntax error / constraint failure
            conn.execute("INSERT INTO entity_mentions (mention_id, source_type) VALUES ('bad', 'bad')")
    except Exception:
        pass

    # men_rb_02 should have been rolled back
    with temp_db._get_connection() as conn:
        res = conn.execute("SELECT * FROM entity_mentions WHERE mention_id = 'men_rb_02'").fetchone()
        assert res is None


# -----------------------------------------------------------------------------
# 8. Evaluation Metrics Calculation Tests
# -----------------------------------------------------------------------------
def test_evaluation_metrics_ner_calculation():
    ground_truth = [
        {"start": 0, "end": 11, "type": "PLAYER", "surface": "Virat Kohli"},
        {"start": 16, "end": 21, "type": "TEAM", "surface": "India"},
    ]
    predicted = [
        {"start": 0, "end": 11, "type": "PLAYER", "surface": "Virat Kohli"},
        {"start": 16, "end": 21, "type": "TEAM", "surface": "India"},
        {"start": 30, "end": 35, "type": "VENUE", "surface": "Dubai"},  # False Positive
    ]

    metrics = compute_ner_metrics(ground_truth, predicted)
    assert metrics.true_positives == 2
    assert metrics.false_positives == 1
    assert metrics.false_negatives == 0
    assert metrics.overall.precision == pytest.approx(2 / 3, 0.01)
    assert metrics.overall.recall == 1.0


def test_evaluation_metrics_sentiment_calculation():
    gt = ["POSITIVE", "NEGATIVE", "NEUTRAL", "POSITIVE"]
    pr = ["POSITIVE", "NEGATIVE", "NEUTRAL", "NEUTRAL"]

    res = compute_sentiment_metrics(gt, pr)
    assert res.accuracy == 0.75
    assert res.macro_f1 > 0.60
    assert "POSITIVE" in res.per_class
