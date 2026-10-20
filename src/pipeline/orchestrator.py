"""Acquisition Runner and Idempotent Ingestion Orchestrator for T20 Cricket Intelligence.

Coordinates discovery, fetching, adapter execution, entity linking,
transactional database persistence, and per-source quality metrics.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.adapters.commentary_adapter import CommentaryAdapter
from src.adapters.cricsheet_adapter import CricsheetAdapter
from src.adapters.news_adapter import NewsArticleAdapter
from src.models.canonical import IngestionRun, SourceRecord
from src.pipeline.config import SourceCategory, SourceConfig, SourceRegistry
from src.pipeline.discovery import DiscoveryEngine
from src.pipeline.entity_linker import EntityLinker
from src.pipeline.fetcher import FetchError, FetchResult, ResponsibleFetcher, RobotsDisallowedError
from src.pipeline.state_machine import DiscoveredUrlRecord, ResourceState
from src.storage.parquet_manager import ParquetStorageManager
from src.storage.sqlite_manager import SQLiteStorageManager

logger = logging.getLogger(__name__)


@dataclass
class SourceRunMetrics:
    """Operational execution metrics for a single source ingestion run."""
    source_id: str
    urls_discovered: int = 0
    urls_queued: int = 0
    fetch_attempts: int = 0
    fetch_success: int = 0
    http_failures: int = 0
    parse_failures: int = 0
    validation_failures: int = 0
    records_extracted: int = 0
    records_validated: int = 0
    records_ingested: int = 0
    records_skipped: int = 0
    records_updated: int = 0
    retry_count: int = 0
    duration_sec: float = 0.0
    errors: List[str] = field(default_factory=list)


class AcquisitionOrchestrator:
    """Central orchestrator for the T20 Cricket acquisition pipeline."""

    def __init__(
        self,
        registry: SourceRegistry,
        storage: SQLiteStorageManager,
        parquet: Optional[ParquetStorageManager] = None,
        fetcher: Optional[ResponsibleFetcher] = None,
        discovery_engine: Optional[DiscoveryEngine] = None,
    ):
        self.registry = registry
        self.storage = storage
        self.parquet = parquet
        self.fetcher = fetcher or ResponsibleFetcher()
        self.discovery_engine = discovery_engine or DiscoveryEngine(
            fetch_func=lambda url: self._simple_discovery_fetch(url)
        )
        self.entity_linker = EntityLinker(storage=storage)

        # Adapters
        self.cricsheet_adapter = CricsheetAdapter()
        self.news_adapter = NewsArticleAdapter()
        self.commentary_adapter = CommentaryAdapter()

    def _simple_discovery_fetch(self, url: str) -> Tuple[int, bytes, Dict[str, str]]:
        """Internal helper for discovery fetching."""
        # Finds matching source config or uses default
        cfg = None
        for s in self.registry.sources.values():
            if any(url.startswith(d) or d in url for d in (s.discovery_endpoints or [s.base_url])):
                cfg = s
                break
        if not cfg:
            cfg = list(self.registry.sources.values())[0]
        res = self.fetcher.fetch(url, cfg)
        return res.status_code, res.content, res.headers

    def run_source(
        self,
        source_id: str,
        dry_run: bool = False,
        resume: bool = False,
        limit: Optional[int] = None,
        mock_payloads: Optional[Dict[str, bytes]] = None,
    ) -> SourceRunMetrics:
        """
        Executes end-to-end acquisition for a specific source.
        
        Args:
            source_id: Registered source identifier.
            dry_run: If True, executes discovery, fetch, parse, and validate without persistent write.
            resume: If True, resets RETRY_PENDING and FAILED URLs back to QUEUED before running.
            limit: Maximum number of URLs to process.
            mock_payloads: Optional in-memory payloads for deterministic testing.
            
        Returns:
            SourceRunMetrics summary.
        """
        source = self.registry.get_source(source_id)
        if not source:
            raise KeyError(f"Source '{source_id}' not found in registry")

        metrics = SourceRunMetrics(source_id=source_id)
        start_time = time.time()
        now_utc = datetime.now(timezone.utc)

        self.registry.update_crawl_timestamps(source_id, attempted_at=now_utc)

        # 1. Start Ingestion Run Audit
        run: Optional[IngestionRun] = None
        if not dry_run:
            run = self.storage.start_ingestion_run(source_name=source_id)

        try:
            # 2. Resumption setup
            if resume:
                reset_count = self.storage.reset_retryable_urls(source_id=source_id)
                logger.info(f"Resumed {reset_count} retryable/failed URLs for {source_id}")

            # 3. Discovery Stage
            discovered = self.discovery_engine.discover_from_source(source, custom_payloads=mock_payloads)
            metrics.urls_discovered = len(discovered)
            if discovered and not dry_run:
                new_cnt, _ = self.storage.record_discovered_urls(discovered)
                logger.info(f"Recorded {new_cnt} newly discovered URLs for {source_id}")

            # 4. Fetch Queue
            # Get pending URLs (DISCOVERED, QUEUED, or RETRY_PENDING)
            pending_urls: List[DiscoveredUrlRecord] = []
            if not dry_run:
                # First transition any newly discovered URLs to QUEUED
                disc_records = self.storage.get_urls_by_state(source_id=source_id, state=ResourceState.DISCOVERED)
                for d in disc_records:
                    self.storage.transition_url_state(d.url_id, ResourceState.QUEUED)

                pending_urls = self.storage.get_urls_by_state(
                    source_id=source_id, state=ResourceState.QUEUED, limit=limit
                )
            else:
                # Dry run in-memory queue
                pending_urls = discovered[:limit] if limit else discovered

            metrics.urls_queued = len(pending_urls)
            logger.info(f"Processing {len(pending_urls)} URLs for source {source_id} (dry_run={dry_run})")

            # 5. Process Each Resource in Queue
            for item in pending_urls:
                self._process_resource(
                    item=item,
                    source=source,
                    metrics=metrics,
                    dry_run=dry_run,
                    mock_payloads=mock_payloads,
                )

            # Finalize run metrics
            metrics.duration_sec = time.time() - start_time
            if not dry_run and run:
                run.status = "completed" if metrics.http_failures == 0 and metrics.parse_failures == 0 else "partial"
                run.completed_at_utc = datetime.now(timezone.utc)
                run.records_extracted = metrics.records_extracted
                run.records_ingested = metrics.records_ingested
                run.records_skipped = metrics.records_skipped
                if metrics.errors:
                    run.error_message = "; ".join(metrics.errors[:5])
                self.storage.update_ingestion_run(run)

            self.registry.update_crawl_timestamps(source_id, succeeded_at=datetime.now(timezone.utc))
            return metrics

        except Exception as e:
            metrics.duration_sec = time.time() - start_time
            metrics.errors.append(str(e))
            logger.exception(f"Pipeline run failed for source {source_id}: {e}")
            if not dry_run and run:
                run.status = "failed"
                run.completed_at_utc = datetime.now(timezone.utc)
                run.error_message = str(e)
                self.storage.update_ingestion_run(run)
            return metrics

    def _process_resource(
        self,
        item: DiscoveredUrlRecord,
        source: SourceConfig,
        metrics: SourceRunMetrics,
        dry_run: bool,
        mock_payloads: Optional[Dict[str, bytes]] = None,
    ) -> None:
        """Processes a single discovered item through fetch -> parse -> validate -> ingest."""
        url_id = item.url_id
        target_url = item.canonical_url or item.raw_url

        try:
            # 1. Fetch Stage
            metrics.fetch_attempts += 1
            if not dry_run:
                self.storage.transition_url_state(url_id, ResourceState.FETCHED, increment_attempt=True)

            payload_bytes: bytes
            http_status = 200
            etag = None
            last_modified = None
            content_hash = ""

            if mock_payloads and (target_url in mock_payloads or item.raw_url in mock_payloads):
                payload_bytes = mock_payloads.get(target_url) or mock_payloads[item.raw_url]
                content_hash = hashlib_sha256(payload_bytes)
            else:
                fetch_res = self.fetcher.fetch(
                    target_url,
                    source_config=source,
                    etag=item.etag,
                    last_modified=item.last_modified,
                )
                http_status = fetch_res.status_code
                if fetch_res.is_not_modified:
                    metrics.records_skipped += 1
                    if not dry_run:
                        self.storage.transition_url_state(
                            url_id,
                            ResourceState.SKIPPED,
                            http_status=304,
                            error_message="HTTP 304 Not Modified",
                        )
                    return

                payload_bytes = fetch_res.content
                etag = fetch_res.etag
                last_modified = fetch_res.last_modified
                content_hash = fetch_res.content_hash

            metrics.fetch_success += 1

            # 2. Parse Stage
            if not dry_run:
                self.storage.transition_url_state(url_id, ResourceState.PARSED, content_hash=content_hash)

            # Route by adapter
            if source.adapter_id == "news" or source.category == SourceCategory.NEWS:
                article, paragraphs, prov = self.news_adapter.parse_html(
                    html_content=payload_bytes,
                    canonical_url=target_url,
                )
                metrics.records_extracted += 1

                # 3. Validation Stage
                if not dry_run:
                    self.storage.transition_url_state(url_id, ResourceState.VALIDATED)
                metrics.records_validated += 1

                # 4. Entity Linking Stage
                link_candidate = self.entity_linker.resolve_match_link(
                    headline=article.headline,
                    full_text=article.full_text,
                    published_at_utc=article.published_at_utc,
                )
                if link_candidate:
                    logger.info(
                        f"Resolved article '{article.headline[:35]}...' -> Match {link_candidate.match_id} "
                        f"(Confidence: {link_candidate.confidence})"
                    )

                # 5. Ingestion Stage
                if not dry_run:
                    self.storage.record_provenance(prov)
                    applied, msg, art_id = self.storage.upsert_article_with_paragraphs(
                        article, paragraphs, allow_update=True
                    )

                    if applied and "Updated" in msg:
                        metrics.records_updated += 1
                        metrics.records_ingested += 1
                        self.storage.transition_url_state(url_id, ResourceState.INGESTED, http_status=http_status)
                    elif applied:
                        metrics.records_ingested += 1
                        self.storage.transition_url_state(url_id, ResourceState.INGESTED, http_status=http_status)
                    else:
                        metrics.records_skipped += 1
                        self.storage.transition_url_state(
                            url_id,
                            ResourceState.SKIPPED,
                            http_status=http_status,
                            error_message=msg,
                        )
                else:
                    metrics.records_ingested += 1

            elif source.adapter_id == "cricsheet" or source.category == SourceCategory.STRUCTURED_DATA:
                cric_res = self.cricsheet_adapter.parse_json_bytes(
                    payload_bytes, source_identifier=target_url
                )
                metrics.records_extracted += 1 + len(cric_res.deliveries)

                if not dry_run:
                    self.storage.transition_url_state(url_id, ResourceState.VALIDATED)
                metrics.records_validated += 1

                if not dry_run:
                    self.storage.record_provenance(cric_res.provenance)
                    for t in cric_res.teams:
                        self.storage.upsert_team(t)
                    for p in cric_res.players:
                        self.storage.upsert_player(p)
                    self.storage.upsert_match(cric_res.match)
                    self.storage.replace_deliveries_for_match(cric_res.match.match_id, cric_res.deliveries)

                    # Update Parquet files if manager is configured
                    if self.parquet:
                        self.parquet.append_deliveries(cric_res.deliveries)
                        self.parquet.append_matches([cric_res.match])

                    self.storage.transition_url_state(url_id, ResourceState.INGESTED, http_status=http_status)
                    metrics.records_ingested += 1
                else:
                    metrics.records_ingested += 1

            elif source.adapter_id == "commentary" or source.category == SourceCategory.COMMENTARY:
                # Match hint can be derived or mocked
                match_id = item.metadata.get("match_id", "match_t20_comm_001")
                entries, unparsed = self.commentary_adapter.parse_raw_text(
                    raw_text=payload_bytes.decode("utf-8", errors="replace"),
                    match_id=match_id,
                )
                metrics.records_extracted += len(entries)

                if not dry_run:
                    self.storage.transition_url_state(url_id, ResourceState.VALIDATED)
                metrics.records_validated += len(entries)

                if not dry_run:
                    self.storage.insert_commentary_batch(entries)
                    self.storage.transition_url_state(url_id, ResourceState.INGESTED, http_status=http_status)
                    metrics.records_ingested += len(entries)
                else:
                    metrics.records_ingested += len(entries)

        except FetchError as e:
            metrics.http_failures += 1
            metrics.retry_count += 1
            metrics.errors.append(f"Fetch failure on {target_url}: {e}")
            logger.warning(f"Fetch failure on {target_url}: {e}")
            if not dry_run:
                # If retry count is within limit, set RETRY_PENDING
                if item.attempt_count < source.max_retries:
                    self.storage.transition_url_state(
                        url_id, ResourceState.RETRY_PENDING, error_message=str(e)
                    )
                else:
                    self.storage.transition_url_state(
                        url_id, ResourceState.FAILED, error_message=str(e)
                    )

        except Exception as e:
            metrics.parse_failures += 1
            metrics.errors.append(f"Parsing/Validation failure on {target_url}: {e}")
            logger.exception(f"Processing error on {target_url}: {e}")
            if not dry_run:
                self.storage.transition_url_state(
                    url_id, ResourceState.FAILED, error_message=str(e)
                )


def hashlib_sha256(data: bytes) -> str:
    """Helper to compute sha256 hex string."""
    import hashlib
    return hashlib.sha256(data).hexdigest()
