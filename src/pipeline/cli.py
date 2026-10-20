"""Command-Line Interface for T20 Cricket Intelligence Acquisition Pipeline.

Provides operational commands for running the pipeline, dry runs, listing sources,
inspecting failures, reporting metrics, data validation, and live smoke testing.
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.pipeline.config import SourceRegistry
from src.pipeline.fetcher import ResponsibleFetcher
from src.pipeline.orchestrator import AcquisitionOrchestrator
from src.storage.parquet_manager import ParquetStorageManager
from src.storage.sqlite_manager import SQLiteStorageManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("pipeline_cli")


def list_sources_cmd(args: argparse.Namespace) -> int:
    """Lists configured sources and their operational parameters."""
    registry = SourceRegistry(args.config)
    sources = registry.list_sources()

    print("\n" + "=" * 80)
    print(f"{'SOURCE ID':<16} {'CATEGORY':<16} {'ADAPTER':<12} {'RATE (RPS)':<12} {'ENABLED':<8} {'LICENSE'}")
    print("=" * 80)
    for s in sources:
        enabled_str = "[YES]" if s.enabled else "[NO]"
        print(f"{s.source_id:<16} {s.category.value:<16} {s.adapter_id:<12} {s.rate_limit_rps:<12.2f} {enabled_str:<8} {s.license_tag}")
        if s.discovery_endpoints:
            for ep in s.discovery_endpoints[:2]:
                print(f"  -> Discovery: {ep}")
    print("=" * 80 + "\n")
    return 0


def run_pipeline_cmd(args: argparse.Namespace) -> int:
    """Runs the ingestion pipeline for a specified source or all enabled sources."""
    registry = SourceRegistry(args.config)
    storage = SQLiteStorageManager(args.db_path)
    parquet = ParquetStorageManager(args.parquet_dir) if args.parquet_dir else None
    orchestrator = AcquisitionOrchestrator(registry=registry, storage=storage, parquet=parquet)

    target_sources = [args.source] if args.source else [s.source_id for s in registry.list_sources(enabled_only=True)]

    if not target_sources:
        print("No sources selected or enabled. Run 'list' to see available sources.")
        return 1

    overall_success = True
    print("\nStarting Acquisition Pipeline Execution...")
    print(f"Database: {args.db_path} | Dry Run: {args.dry_run} | Resume: {args.resume}\n")

    for src_id in target_sources:
        print(f">>> Running source: {src_id} ...")
        metrics = orchestrator.run_source(
            source_id=src_id,
            dry_run=args.dry_run,
            resume=args.resume,
            limit=args.limit,
        )

        print(f"    Discovered: {metrics.urls_discovered} | Queued: {metrics.urls_queued}")
        print(f"    Fetches: {metrics.fetch_attempts} (Success: {metrics.fetch_success}, Failures: {metrics.http_failures})")
        print(f"    Extracted: {metrics.records_extracted} | Validated: {metrics.records_validated}")
        print(f"    Ingested: {metrics.records_ingested} (Updated: {metrics.records_updated}) | Skipped: {metrics.records_skipped}")
        print(f"    Duration: {metrics.duration_sec:.2f}s")
        if metrics.errors:
            print(f"    Errors ({len(metrics.errors)}): {metrics.errors[0]}")
            overall_success = False
        print("-" * 60)

    print("\nPipeline run finished.\n")
    return 0 if overall_success else 1


def stats_cmd(args: argparse.Namespace) -> int:
    """Reports ingestion and quality statistics."""
    storage = SQLiteStorageManager(args.db_path)
    metrics = storage.get_source_metrics(source_id=args.source)

    print("\n" + "=" * 60)
    print(f"INGESTION & DATA QUALITY REPORT: {metrics['source_id']}")
    print("=" * 60)
    print(f"Total Discovered URLs:  {metrics['total_discovered']}")
    print(f"Total Fetch Attempts:   {metrics['total_attempts']}")
    print(f"HTTP Errors:            {metrics['http_errors']}")
    print(f"Total Failures:         {metrics['total_errors']}")
    print("-" * 60)
    print("State Distribution:")
    for st, count in metrics.get("states", {}).items():
        print(f"  - {st:<16} : {count}")
    print("-" * 60)
    print("Entity Ingestion Counts:")
    print(f"  - Matches Stored:     {metrics['matches_stored']}")
    print(f"  - Deliveries Stored:  {metrics['deliveries_stored']}")
    print(f"  - Articles Stored:    {metrics['articles_stored']}")
    print(f"  - Article Revisions:  {metrics['article_revisions']}")
    print(f"  - Commentary Stored:  {metrics['commentary_stored']}")
    print("=" * 60 + "\n")
    return 0


def inspect_failed_cmd(args: argparse.Namespace) -> int:
    """Displays failed URLs and their error diagnostics."""
    storage = SQLiteStorageManager(args.db_path)
    from src.pipeline.state_machine import ResourceState

    failed_records = storage.get_urls_by_state(source_id=args.source, state=ResourceState.FAILED, limit=args.limit or 50)
    print("\n" + "=" * 80)
    print(f"FAILED RESOURCES REPORT ({len(failed_records)} entries)")
    print("=" * 80)
    if not failed_records:
        print("No failed resources found! Pipeline is clean.")
    else:
        for f in failed_records:
            print(f"URL: {f.canonical_url}")
            print(f"  Source: {f.source_id} | Attempts: {f.attempt_count} | HTTP Status: {f.http_status}")
            print(f"  Last Error: {f.error_message}")
            print("-" * 80)
    print()
    return 0


def validate_cmd(args: argparse.Namespace) -> int:
    """Validates structural and relational integrity of previously ingested records."""
    storage = SQLiteStorageManager(args.db_path)
    print("\nValidating Ingested Data Integrity...")

    m_cnt = storage.get_match_count()
    d_cnt = storage.get_delivery_count()
    a_cnt = storage.get_article_count()
    c_cnt = storage.get_commentary_count()

    print(f"Ground-Truth Matches: {m_cnt}")
    print(f"Deliveries:           {d_cnt}")
    print(f"News Articles:        {a_cnt}")
    print(f"Commentary Entries:   {c_cnt}")

    issues = []
    # Check deliveries without match
    with storage._get_connection() as conn:
        orphaned_del = conn.execute(
            "SELECT COUNT(*) FROM deliveries WHERE match_id NOT IN (SELECT match_id FROM matches)"
        ).fetchone()[0]
        if orphaned_del > 0:
            issues.append(f"Found {orphaned_del} orphaned delivery records without parent match")

        # Check total_runs delivery consistency
        bad_totals = conn.execute(
            "SELECT COUNT(*) FROM deliveries WHERE total_runs != (batter_runs + extra_runs)"
        ).fetchone()[0]
        if bad_totals > 0:
            issues.append(f"Found {bad_totals} deliveries violating total_runs == batter_runs + extra_runs")

        # Check articles without paragraphs
        empty_articles = conn.execute(
            "SELECT COUNT(*) FROM articles WHERE article_id NOT IN (SELECT DISTINCT article_id FROM article_paragraphs)"
        ).fetchone()[0]
        if empty_articles > 0:
            issues.append(f"Found {empty_articles} articles missing segmented paragraphs")

    print("-" * 60)
    if not issues:
        print("[SUCCESS] All relational integrity checks and schema invariants passed perfectly!")
        return 0
    else:
        print("[WARNING] Data validation issues detected:")
        for issue in issues:
            print(f"  - {issue}")
        return 1


def smoke_test_cmd(args: argparse.Namespace) -> int:
    """
    Explicitly invoked live smoke test against permitted source endpoints.
    Disabled by default; respects polite rate limits and verifies live server connectivity.
    """
    if not args.confirm_live:
        print("\n[SMOKE TEST BLOCKED]: Live smoke tests require explicit '--confirm-live' confirmation.")
        print("This prevents accidental live requests during automated builds or offline development.\n")
        return 1

    registry = SourceRegistry(args.config)
    source = registry.get_source(args.source)
    if not source:
        print(f"Error: Source '{args.source}' not found in configuration.")
        return 1

    fetcher = ResponsibleFetcher()
    test_url = source.discovery_endpoints[0] if source.discovery_endpoints else source.base_url

    print("\n" + "=" * 70)
    print(f"LIVE SMOKE TEST: {source.name} ({source.source_id})")
    print(f"Target URL:     {test_url}")
    print(f"Rate Limit:     {source.rate_limit_rps} RPS")
    print(f"User Agent:     {fetcher.user_agent}")
    print("=" * 70)

    try:
        # Check robots.txt first
        allowed = fetcher.check_robots_allowed(test_url)
        print(f"Robots.txt Check:  {'ALLOWED' if allowed else 'DISALLOWED'}")
        if not allowed:
            print("[SMOKE TEST FAILED]: Target URL is disallowed by publisher robots.txt directives.")
            return 1

        print("Executing single polite conditional fetch...")
        res = fetcher.fetch(test_url, source_config=source)
        print(f"HTTP Status:       {res.status_code}")
        print(f"Response Size:     {len(res.content)} bytes")
        print(f"ETag:              {res.etag or 'None'}")
        print(f"Duration:          {res.duration_sec:.2f}s")
        print(f"Content SHA-256:   {res.content_hash[:16]}...")
        print("[SMOKE TEST PASSED]: Live endpoint responded successfully within policy bounds!\n")
        return 0

    except Exception as e:
        print(f"[SMOKE TEST FAILED]: Error connecting to {test_url}: {e}\n")
        return 1


def main() -> int:
    """CLI Entry point."""
    parser = argparse.ArgumentParser(
        prog="python -m src.pipeline",
        description="T20 Cricket Intelligence Acquisition & Ingestion Pipeline CLI",
    )
    parser.add_argument("--config", default="config/sources.yaml", help="Path to sources.yaml configuration")
    parser.add_argument("--db-path", default="data/cricket_intel.db", help="Path to SQLite database")
    parser.add_argument("--parquet-dir", default=None, help="Optional directory for Parquet storage")

def process_text_cmd(args: argparse.Namespace) -> int:
    """Executes the NLP pipeline on acquired texts."""
    from src.nlp.processing_pipeline import NLPPipeline

    storage = SQLiteStorageManager(args.db_path)
    pipeline = NLPPipeline(storage=storage)

    print("\nStarting Cricket NLP Pipeline...")
    print(f"Database: {args.db_path} | Dry Run: {args.dry_run} | All Records: {args.all}\n")

    metrics = pipeline.process_records(
        source_id=args.source,
        process_all=args.all,
        dry_run=args.dry_run,
        limit=args.limit,
    )

    print("-" * 60)
    print(f"Records Processed:        {metrics.records_processed}")
    print(f"Normalized Texts Created: {metrics.normalized_texts_created}")
    print(f"Entity Mentions Extracted: {metrics.mentions_extracted}")
    print(f"  - Resolved Mentions:    {metrics.mentions_resolved}")
    print(f"  - Ambiguous Mentions:   {metrics.mentions_ambiguous}")
    print(f"Sentiment Records:        {metrics.sentiment_records_created}")
    print(f"Duration:                 {metrics.duration_sec:.2f}s")
    if metrics.errors:
        print(f"Errors Encountered:       {len(metrics.errors)} (first: {metrics.errors[0]})")
    print("-" * 60 + "\n")
    return 0 if not metrics.errors else 1


def nlp_stats_cmd(args: argparse.Namespace) -> int:
    """Reports aggregated statistics from derived NLP tables."""
    storage = SQLiteStorageManager(args.db_path)
    metrics = storage.get_nlp_metrics()

    print("\n" + "=" * 60)
    print("NLP & ENTITY RESOLUTION METRICS REPORT")
    print("=" * 60)
    print(f"Normalized Texts:        {metrics['normalized_texts_count']}")
    print(f"Total Entity Mentions:   {metrics['total_mentions']}")
    print(f"  - Resolved Mentions:   {metrics['resolved_mentions']}")
    print(f"  - Ambiguous Mentions:  {metrics['ambiguous_mentions']}")
    print(f"  - Unresolved Mentions: {metrics['unresolved_mentions']}")
    print(f"Resolution Rate:         {metrics['resolution_rate'] * 100:.1f}%")
    print(f"Ambiguity Rate:          {metrics['ambiguity_rate'] * 100:.1f}%")
    print("-" * 60)
    print(f"Sentiment Baseline Records: {metrics['total_sentiment_records']}")
    print(f"  - Positive Sentiment:  {metrics['positive_sentiment_count']}")
    print(f"  - Neutral Sentiment:   {metrics['neutral_sentiment_count']}")
    print(f"  - Negative Sentiment:  {metrics['negative_sentiment_count']}")
    print("=" * 60 + "\n")
    return 0


def nlp_validate_cmd(args: argparse.Namespace) -> int:
    """Validates integrity and invariants of stored NLP outputs."""
    storage = SQLiteStorageManager(args.db_path)
    print("\nValidating Stored NLP Integrity...")

    issues = []
    with storage._get_connection() as conn:
        # 1. Invalid mention spans (end_char < start_char)
        bad_spans = conn.execute(
            "SELECT COUNT(*) FROM entity_mentions WHERE end_char < start_char;"
        ).fetchone()[0]
        if bad_spans > 0:
            issues.append(f"Found {bad_spans} entity mentions with invalid spans (end_char < start_char)")

        # 2. Resolved mentions with null resolved_id
        inconsistent_res = conn.execute(
            "SELECT COUNT(*) FROM entity_mentions WHERE resolution_status = 'RESOLVED' AND resolved_id IS NULL;"
        ).fetchone()[0]
        if inconsistent_res > 0:
            issues.append(f"Found {inconsistent_res} mentions marked RESOLVED but missing resolved_id")

        # 3. Sentiment scores out of range [-1.0, 1.0]
        bad_scores = conn.execute(
            "SELECT COUNT(*) FROM sentiment_baselines WHERE compound_score < -1.0 OR compound_score > 1.0;"
        ).fetchone()[0]
        if bad_scores > 0:
            issues.append(f"Found {bad_scores} sentiment records with compound_score outside [-1.0, 1.0]")

    if not issues:
        print("[SUCCESS] All NLP data structures, span invariants, and resolution constraints validated perfectly!\n")
        return 0
    else:
        print("[WARNING] Invariant issues detected in NLP tables:")
        for iss in issues:
            print(f"  - {iss}")
        print()
        return 1


def resolve_entity_cmd(args: argparse.Namespace) -> int:
    """Resolves an entity mention string and displays candidate evaluations."""
    from src.nlp.entity_resolver import EntityResolver
    from src.nlp.gazetteer import CricketGazetteer
    from src.nlp.schemas import EntityMentionRecord, EntityType

    storage = SQLiteStorageManager(args.db_path)
    gazetteer = CricketGazetteer(storage=storage)
    resolver = EntityResolver(gazetteer=gazetteer)

    surface = args.mention.strip()
    mention = EntityMentionRecord(
        mention_id="cli_query",
        source_type="cli",
        source_id="cli_input",
        entity_type=EntityType.PLAYER,
        surface_text=surface,
        start_char=0,
        end_char=len(surface),
        confidence=0.5,
    )

    teams_in_doc = set()
    context_text = getattr(args, "context", None)
    if context_text:
        from src.nlp.ner import CricketNER
        ner = CricketNER(gazetteer=gazetteer)
        context_mentions = ner.extract_mentions(context_text, source_type="cli", source_id="context")
        for cm in context_mentions:
            if cm.entity_type == EntityType.TEAM:
                teams_in_doc.add(cm.surface_text.lower())
                for entry in gazetteer.lookup_alias(cm.surface_text):
                    if entry.entity_type == EntityType.TEAM:
                        teams_in_doc.add(entry.canonical_id)

    resolved, audits = resolver._resolve_single_mention(mention, teams_in_doc=teams_in_doc)

    print("\n" + "=" * 60)
    print(f"ENTITY RESOLUTION QUERY: '{surface}'")
    print("=" * 60)
    print(f"Resolution Status: {resolved.resolution_status.value}")
    print(f"Resolved ID:       {resolved.resolved_id or 'None'}")
    print(f"Confidence:        {resolved.confidence}")
    print("-" * 60)
    print(f"Candidate Evaluations ({len(audits)}):")
    for a in audits:
        winner_mark = "[WINNER]" if a.is_winner else "        "
        print(f"  {winner_mark} Candidate: {a.candidate_id:<28} Score: {a.score:.3f}")
        for k, v in a.evidence.items():
            print(f"             - {k}: {v}")
    print("=" * 60 + "\n")
    return 0


def main() -> int:
    """CLI Entry point."""
    parser = argparse.ArgumentParser(
        prog="python -m src.pipeline",
        description="T20 Cricket Intelligence Acquisition & Ingestion Pipeline CLI",
    )
    parser.add_argument("--config", default="config/sources.yaml", help="Path to sources.yaml configuration")
    parser.add_argument("--db-path", default="data/cricket_intel.db", help="Path to SQLite database")
    parser.add_argument("--parquet-dir", default=None, help="Optional directory for Parquet storage")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # list
    subparsers.add_parser("list", help="List registered data sources and crawl settings")

    # run
    run_parser = subparsers.add_parser("run", help="Run acquisition pipeline")
    run_parser.add_argument("--source", default=None, help="Source identifier (defaults to all enabled)")
    run_parser.add_argument("--dry-run", action="store_true", help="Execute without committing writes to database")
    run_parser.add_argument("--resume", action="store_true", help="Resume RETRY_PENDING and FAILED URLs")
    run_parser.add_argument("--limit", type=int, default=None, help="Limit number of items to process")

    # stats
    stats_parser = subparsers.add_parser("stats", help="Show ingestion statistics and data quality metrics")
    stats_parser.add_argument("--source", default=None, help="Source identifier filter")

    # inspect-failed
    inspect_parser = subparsers.add_parser("inspect-failed", help="Inspect failed URLs and error reasons")
    inspect_parser.add_argument("--source", default=None, help="Source identifier filter")
    inspect_parser.add_argument("--limit", type=int, default=50, help="Max entries to display")

    # validate
    subparsers.add_parser("validate", help="Validate relational integrity of ingested records")

    # smoke-test
    smoke_parser = subparsers.add_parser("smoke-test", help="Explicitly test live permitted source connectivity")
    smoke_parser.add_argument("--source", required=True, help="Source identifier to test")
    smoke_parser.add_argument("--confirm-live", action="store_true", help="Required confirmation to make live request")

    # NLP commands
    proc_parser = subparsers.add_parser("process-text", help="Run cricket NLP pipeline on acquired texts")
    proc_parser.add_argument("--source", default=None, help="Optional source filter")
    proc_parser.add_argument("--all", action="store_true", help="Process both news articles and commentary")
    proc_parser.add_argument("--dry-run", action="store_true", help="Compute NLP outputs without database writes")
    proc_parser.add_argument("--limit", type=int, default=None, help="Limit number of items to process")

    subparsers.add_parser("nlp-stats", help="Show aggregated NLP and entity resolution metrics")
    subparsers.add_parser("nlp-validate", help="Validate invariant constraints of stored NLP records")

    res_parser = subparsers.add_parser("resolve-entity", help="Resolve a mention string and inspect candidate ranking")
    res_parser.add_argument("--mention", required=True, help="Entity mention surface text to resolve")
    res_parser.add_argument("--context", default="", help="Optional context text (e.g. sentence containing team name)")

    args = parser.parse_args()

    commands = {
        "list": list_sources_cmd,
        "run": run_pipeline_cmd,
        "stats": stats_cmd,
        "inspect-failed": inspect_failed_cmd,
        "validate": validate_cmd,
        "smoke-test": smoke_test_cmd,
        "process-text": process_text_cmd,
        "nlp-stats": nlp_stats_cmd,
        "nlp-validate": nlp_validate_cmd,
        "resolve-entity": resolve_entity_cmd,
    }

    cmd_fn = commands.get(args.command)
    if cmd_fn:
        return cmd_fn(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
