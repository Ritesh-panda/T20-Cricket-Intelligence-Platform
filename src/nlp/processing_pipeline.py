"""End-to-End NLP Processing Pipeline for T20 Cricket Intelligence.

Coordinates text normalization, tokenization, entity recognition, entity resolution,
and sentiment/framing baselines with idempotent transactional persistence.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from src.nlp.cricket_tokenizer import CricketTokenizer, TokenizationMode
from src.nlp.entity_resolver import EntityResolver
from src.nlp.gazetteer import CricketGazetteer
from src.nlp.ner import CricketNER
from src.nlp.schemas import (
    EntityMentionRecord,
    EntityResolutionRecord,
    EntityType,
    NLPRunRecord,
    NormalizedTextRecord,
    SentimentBaselineRecord,
)
from src.nlp.sentiment import CricketSentimentBaseline
from src.nlp.text_cleaner import CricketTextCleaner
from src.storage.sqlite_manager import SQLiteStorageManager

logger = logging.getLogger(__name__)


@dataclass
class NLPExecutionMetrics:
    """Summary metrics for an NLP pipeline run."""
    run_id: str
    records_processed: int = 0
    normalized_texts_created: int = 0
    mentions_extracted: int = 0
    mentions_resolved: int = 0
    mentions_ambiguous: int = 0
    sentiment_records_created: int = 0
    duration_sec: float = 0.0
    errors: List[str] = field(default_factory=list)


class NLPPipeline:
    """Orchestrates end-to-end NLP processing across articles and commentary."""

    def __init__(
        self,
        storage: SQLiteStorageManager,
        gazetteer: Optional[CricketGazetteer] = None,
        pipeline_version: str = "0.1.0",
    ):
        self.storage = storage
        self.pipeline_version = pipeline_version
        self.gazetteer = gazetteer or CricketGazetteer(storage=storage)
        self.cleaner = CricketTextCleaner()
        self.editorial_tokenizer = CricketTokenizer(mode=TokenizationMode.EDITORIAL)
        self.commentary_tokenizer = CricketTokenizer(mode=TokenizationMode.COMMENTARY)
        self.ner = CricketNER(gazetteer=self.gazetteer, pipeline_version=pipeline_version)
        self.resolver = EntityResolver(gazetteer=self.gazetteer)
        self.sentiment_engine = CricketSentimentBaseline(pipeline_version=pipeline_version)

    def process_records(
        self,
        source_id: Optional[str] = None,
        process_all: bool = False,
        dry_run: bool = False,
        limit: Optional[int] = None,
    ) -> NLPExecutionMetrics:
        """
        Executes NLP pipeline on pending paragraphs and commentary.
        
        Args:
            source_id: Optional source filter.
            process_all: If True, processes both news and commentary.
            dry_run: If True, computes NLP outputs without database writes.
            limit: Maximum records to process.
            
        Returns:
            NLPExecutionMetrics summary.
        """
        start_time = time.time()
        run_record: Optional[NLPRunRecord] = None
        if not dry_run:
            run_record = self.storage.start_nlp_run()

        metrics = NLPExecutionMetrics(run_id=run_record.run_id if run_record else "dry_run")

        try:
            # 1. Fetch records to process
            paragraphs = self.storage.get_paragraphs_for_processing(limit=limit)
            commentary = self.storage.get_commentary_for_processing(limit=limit) if process_all else []

            total_items = len(paragraphs) + len(commentary)
            logger.info(f"NLP Pipeline starting: {len(paragraphs)} paragraphs, {len(commentary)} commentary entries (dry_run={dry_run})")

            # 2. Process Paragraphs
            for p in paragraphs:
                self._process_single_item(
                    raw_text=p["text"],
                    source_id=p["paragraph_id"],
                    source_type="article_paragraph",
                    metrics=metrics,
                    dry_run=dry_run,
                )

            # 3. Process Commentary
            for c in commentary:
                self._process_single_item(
                    raw_text=c["text"],
                    source_id=c["commentary_id"],
                    source_type="commentary_entry",
                    metrics=metrics,
                    dry_run=dry_run,
                )

            metrics.duration_sec = time.time() - start_time
            if not dry_run and run_record:
                run_record.status = "completed"
                run_record.completed_at_utc = datetime.now(timezone.utc)
                run_record.records_processed = metrics.records_processed
                run_record.mentions_extracted = metrics.mentions_extracted
                run_record.sentiment_scored = metrics.sentiment_records_created
                run_record.errors = metrics.errors
                self.storage.update_nlp_run(run_record)

            return metrics

        except Exception as e:
            metrics.duration_sec = time.time() - start_time
            metrics.errors.append(str(e))
            logger.exception(f"NLP Pipeline run failed: {e}")
            if not dry_run and run_record:
                run_record.status = "failed"
                run_record.completed_at_utc = datetime.now(timezone.utc)
                run_record.errors.append(str(e))
                self.storage.update_nlp_run(run_record)
            return metrics

    def _process_single_item(
        self,
        raw_text: str,
        source_id: str,
        source_type: str,
        metrics: NLPExecutionMetrics,
        dry_run: bool,
    ) -> None:
        """Runs full NLP lifecycle for a single text record."""
        try:
            # A. Clean and Normalize
            norm_rec = self.cleaner.create_normalized_record(
                source_id=source_id,
                source_type=source_type,
                raw_text=raw_text,
                pipeline_version=self.pipeline_version,
            )
            cleaned_text = norm_rec.normalized_text

            # B. Tokenize (editorial vs commentary)
            if source_type == "commentary_entry":
                tokens = self.commentary_tokenizer.tokenize(cleaned_text)
            else:
                tokens = self.editorial_tokenizer.tokenize(cleaned_text)

            # C. Named Entity Recognition
            raw_mentions = self.ner.extract_mentions(
                text=cleaned_text,
                source_id=source_id,
                source_type=source_type,
            )

            # D. Entity Resolution
            resolved_mentions, resolution_audits = self.resolver.resolve_mentions(
                mentions=raw_mentions,
                document_text=cleaned_text,
            )

            # E. Sentiment & Performance Framing
            # 1. Document-level sentiment
            doc_sentiment = self.sentiment_engine.score_text(
                text=cleaned_text,
                source_id=source_id,
                source_type=source_type,
                target_entity_id=None,
            )
            sentiment_records: List[SentimentBaselineRecord] = [doc_sentiment]

            # 2. Aspect-targeted sentiment for resolved entities
            resolved_player_team_ids = {
                m.resolved_id for m in resolved_mentions
                if m.resolved_id and m.entity_type in (EntityType.PLAYER, EntityType.TEAM)
            }
            for entity_id in resolved_player_team_ids:
                is_bowling = any("wicket" in t.text.lower() or "bowled" in t.text.lower() for t in tokens)
                aspect_sent = self.sentiment_engine.score_text(
                    text=cleaned_text,
                    source_id=source_id,
                    source_type=source_type,
                    target_entity_id=entity_id,
                    is_bowling_context=is_bowling,
                )
                sentiment_records.append(aspect_sent)

            # F. Persistence
            if not dry_run:
                self.storage.upsert_normalized_text(norm_rec)
                if resolved_mentions:
                    self.storage.upsert_entity_mentions(resolved_mentions)
                if resolution_audits:
                    self.storage.upsert_entity_resolutions(resolution_audits)
                if sentiment_records:
                    self.storage.upsert_sentiment_baselines(sentiment_records)

            # G. Metrics Update
            metrics.records_processed += 1
            metrics.normalized_texts_created += 1
            metrics.mentions_extracted += len(resolved_mentions)
            metrics.mentions_resolved += sum(1 for m in resolved_mentions if m.resolution_status.value == "RESOLVED")
            metrics.mentions_ambiguous += sum(1 for m in resolved_mentions if m.resolution_status.value == "AMBIGUOUS")
            metrics.sentiment_records_created += len(sentiment_records)

        except Exception as e:
            metrics.errors.append(f"Error on {source_id}: {e}")
            logger.warning(f"Error processing {source_id}: {e}")
