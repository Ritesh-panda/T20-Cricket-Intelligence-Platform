"""Command-Line Interface for T20 Cricket Intelligence Acquisition Pipeline.

Provides operational commands for running the pipeline, dry runs, listing sources,
inspecting failures, reporting metrics, data validation, and live smoke testing.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.pipeline.config import SourceRegistry
from src.pipeline.fetcher import ResponsibleFetcher
from src.pipeline.orchestrator import AcquisitionOrchestrator
from src.storage.parquet_manager import ParquetStorageManager
from src.storage.sqlite_manager import SQLiteStorageManager
from src.analytics.schemas import (
    AnalyticsRunRecord,
    CohortRole,
    CricketPerformanceMetrics,
    DiscrepancyCategory,
    MediaAttentionMetrics,
    PreflightCheckResult,
    SufficiencyStatus,
)
from src.analytics.preflight import AnalyticsPreflight
from src.analytics.attention import MediaAttentionCalculator
from src.analytics.performance import CricketPerformanceCalculator
from src.analytics.framing import NarrativeFramingCalculator
from src.analytics.apdi import APDICalculator

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


# -------------------------------------------------------------------------
# Phase 5 CLI Commands
# -------------------------------------------------------------------------

def embed_text_cmd(args: argparse.Namespace) -> int:
    """Executes embedding pipeline on normalized texts."""
    from src.analysis.embedding_models import get_embedding_model
    from src.analysis.embedding_pipeline import EmbeddingPipeline

    storage = SQLiteStorageManager(args.db_path)
    model = get_embedding_model(args.model)
    pipeline = EmbeddingPipeline(storage=storage, embedding_model=model)

    print("\nStarting Semantic Embedding Generation...")
    print(f"Model: {model.model_name} (Test Double: {model.is_test_double}) | Dry Run: {args.dry_run}\n")

    res = pipeline.process_normalized_texts(
        source_type=args.source_type,
        dry_run=args.dry_run,
        limit=args.limit,
    )

    print("-" * 60)
    print("EMBEDDING PIPELINE EXECUTION SUMMARY")
    print("-" * 60)
    print(f"Total Eligible Texts:   {res['total_eligible']}")
    print(f"Embeddings Computed:    {res['embeddings_computed']}")
    print(f"Skipped (Cache Hits):   {res['skipped_cache_hits']}")
    print(f"Dry Run Mode:           {res['dry_run']}")
    print("=" * 60 + "\n")
    return 0


def cluster_topics_cmd(args: argparse.Namespace) -> int:
    """Clusters embedded texts and extracts topic labels."""
    import uuid
    import numpy as np
    from src.analysis.analysis_schemas import CorpusType, TopicAssignmentRecord, TopicClusterRecord, TopicRunRecord
    from src.analysis.topic_clustering import TopicClusterer
    from src.analysis.topic_evaluation import evaluate_topic_clustering
    from src.analysis.topic_labeling import TopicLabeler

    storage = SQLiteStorageManager(args.db_path)
    corpus_type = CorpusType(args.corpus)

    print(f"\nInitiating Topic Clustering for corpus: '{corpus_type.value}'...")

    with storage._get_connection() as conn:
        q = "SELECT e.embedding_id, e.norm_id, e.source_id, e.vector_file_path, e.vector_index, n.normalized_text FROM embedding_records e JOIN normalized_texts n ON e.norm_id = n.norm_id"
        if corpus_type == CorpusType.EDITORIAL:
            q += " WHERE e.source_type = 'article_paragraph'"
        elif corpus_type == CorpusType.COMMENTARY:
            q += " WHERE e.source_type = 'commentary'"
        rows = conn.execute(q).fetchall()

    if not rows:
        print(f"[REPORT] No eligible embedded records found in database for corpus: '{corpus_type.value}'.")
        print("Run 'python -m src.pipeline embed-text' first to populate embeddings.\n")
        return 0

    # Load vectors from cache files
    embeddings_list = []
    valid_rows = []
    for r in rows:
        vpath = r["vector_file_path"]
        vidx = r["vector_index"]
        if vpath and os.path.exists(vpath):
            mat = np.load(vpath)
            if vidx is not None and vidx < len(mat):
                embeddings_list.append(mat[vidx])
                valid_rows.append(r)

    if not embeddings_list:
        print("[WARNING] Embedding records exist in DB but local vector files were not found.")
        return 1

    matrix = np.array(embeddings_list, dtype=np.float32)
    doc_ids = [r["norm_id"] for r in valid_rows]
    doc_texts = [r["normalized_text"] for r in valid_rows]

    clusterer = TopicClusterer(
        algorithm=args.algorithm,
        n_clusters=args.k,
        random_state=42,
    )
    labels = clusterer.fit_predict(matrix)
    distances = clusterer.compute_distances_to_centroid(matrix)

    # Evaluation
    eval_metrics = evaluate_topic_clustering(matrix, labels, clusterer.cluster_centers_)

    # Labeling
    labeler = TopicLabeler(top_n_words=5)
    cluster_keywords = labeler.extract_cluster_keywords(doc_texts, labels)

    run_id = f"topic_run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    run_rec = TopicRunRecord(
        run_id=run_id,
        corpus_type=corpus_type,
        algorithm=args.algorithm,
        n_clusters_requested=args.k if args.algorithm == "kmeans" else None,
        n_clusters_found=eval_metrics.n_clusters,
        n_noise_points=eval_metrics.n_noise,
        parameters_json=json.dumps({"algorithm": args.algorithm, "k": args.k, "random_state": 42}),
        silhouette_score=eval_metrics.silhouette_score,
        davies_bouldin_index=eval_metrics.davies_bouldin_index,
    )

    cluster_recs = []
    for clus_id in sorted(list(set(labels))):
        is_noise = (clus_id == -1)
        kws = cluster_keywords.get(clus_id, [])
        lbl = labeler.generate_topic_label(kws, clus_id)
        rep_ids = labeler.select_representative_documents(doc_ids, labels, distances, clus_id, top_m=3)

        c_rec = TopicClusterRecord(
            cluster_id=f"{run_id}_c{clus_id}",
            run_id=run_id,
            cluster_index=clus_id,
            topic_label=lbl,
            keywords=kws,
            doc_count=eval_metrics.cluster_sizes.get(clus_id, 0),
            representative_doc_ids=rep_ids,
            is_noise=is_noise,
        )
        cluster_recs.append(c_rec)

    # Assignments
    assignment_recs = []
    for i, r in enumerate(valid_rows):
        cid = labels[i]
        c_id_str = f"{run_id}_c{cid}"
        assignment_recs.append(
            TopicAssignmentRecord(
                assignment_id=f"assign_{run_id}_{i}_{r['norm_id']}",
                cluster_id=c_id_str,
                norm_id=r["norm_id"],
                source_id=r["source_id"],
                distance_to_centroid=float(distances[i]),
                membership_score=1.0,
            )
        )

    storage.save_topic_run(run_rec, cluster_recs, assignment_recs)

    print("-" * 60)
    print(f"TOPIC CLUSTERING RUN: {run_id}")
    print("-" * 60)
    print(f"Corpus:          {corpus_type.value}")
    print(f"Algorithm:       {args.algorithm}")
    print(f"Clusters Found:  {eval_metrics.n_clusters}")
    print(f"Noise Documents: {eval_metrics.n_noise} ({eval_metrics.noise_ratio:.1%})")
    print(f"Silhouette:      {eval_metrics.silhouette_score or 'N/A'}")
    print(f"Davies-Bouldin:  {eval_metrics.davies_bouldin_index or 'N/A'}")
    print("-" * 60)
    print("Discovered Clusters:")
    for c in cluster_recs:
        print(f"  Cluster {c.cluster_index:<3} [{c.doc_count:>3} docs] : {c.topic_label}")
        if c.keywords:
            print(f"             Keywords: {', '.join(c.keywords)}")
    print("=" * 60 + "\n")
    return 0


def evaluate_topics_cmd(args: argparse.Namespace) -> int:
    """Displays clustering evaluation metrics."""
    storage = SQLiteStorageManager(args.db_path)
    runs = storage.get_topic_runs()

    print("\n" + "=" * 60)
    print("TOPIC DISCOVERY EVALUATION AUDIT")
    print("=" * 60)

    if not runs:
        print("No topic clustering runs stored in database.\n")
        return 0

    target_run = runs[0] if not args.run_id else next((r for r in runs if r["run_id"] == args.run_id), None)
    if not target_run:
        print(f"Run ID '{args.run_id}' not found.")
        return 1

    print(f"Run ID:          {target_run['run_id']}")
    print(f"Corpus:          {target_run['corpus_type']}")
    print(f"Algorithm:       {target_run['algorithm']}")
    print(f"Clusters Found:  {target_run['n_clusters_found']}")
    print(f"Noise Count:     {target_run['n_noise_points']}")
    print(f"Silhouette:      {target_run['silhouette_score'] or 'N/A'}")
    print(f"Davies-Bouldin:  {target_run['davies_bouldin_index'] or 'N/A'}")
    print(f"Executed At:     {target_run['created_at_utc']}")
    print("-" * 60)

    clusters = storage.get_topic_clusters(run_id=target_run["run_id"])
    print(f"Clusters Detail ({len(clusters)}):")
    for c in clusters:
        kws = json.loads(c["keywords_json"] or "[]")
        print(f"  Index {c['cluster_index']:<2} | Docs: {c['doc_count']:<3} | Label: {c['topic_label']}")
        if kws:
            print(f"           Keywords: {', '.join(kws)}")
    print("=" * 60 + "\n")
    return 0


def narrative_timeline_cmd(args: argparse.Namespace) -> int:
    """Builds and displays narrative evolution timeline points."""
    from src.analysis.narrative_timeline import NarrativeTimelineEngine

    storage = SQLiteStorageManager(args.db_path)
    engine = NarrativeTimelineEngine()

    with storage._get_connection() as conn:
        q = "SELECT article_id, published_at_utc, headline, summary FROM articles"
        rows = [dict(r) for r in conn.execute(q).fetchall()]

    print("\n" + "=" * 60)
    print("NARRATIVE EVOLUTION TIMELINE")
    print("=" * 60)

    if not rows:
        print("No articles present in database to build timeline.")
        print("Timeline observations: 0\n")
        return 0

    articles_data = []
    for r in rows:
        articles_data.append({
            "article_id": r["article_id"],
            "published_at": r.get("published_at_utc"),
            "sentiment_label": "NEUTRAL",
            "sentiment_score": 0.0,
            "entities": [],
            "topic_label": None,
        })

    timeline = engine.build_timeline(articles_data)
    storage.save_timeline_snapshots(timeline)

    print(f"Timeline Observations: {len(timeline)} time buckets\n")
    for pt in timeline:
        print(f"Bucket [{pt.bucket_label}]: {pt.doc_count} documents")
        print(f"  Observed TS: {pt.observed_timestamps_count} | Inferred TS: {pt.inferred_timestamps_count}")
        print(f"  Mean Sentiment: {pt.mean_sentiment:.2f}")
    print("=" * 60 + "\n")
    return 0


def analysis_stats_cmd(args: argparse.Namespace) -> int:
    """Shows aggregated Phase 5 analysis metrics."""
    storage = SQLiteStorageManager(args.db_path)
    metrics = storage.get_analysis_metrics()

    print("\n" + "=" * 60)
    print("PHASE 5 ANALYSIS & NARRATIVE INTELLIGENCE METRICS")
    print("=" * 60)
    print(f"Dense Embedding Records:    {metrics['embedding_records_count']}")
    print(f"Topic Discovery Runs:       {metrics['topic_runs_count']}")
    print(f"Topic Clusters Discovered:  {metrics['topic_clusters_count']}")
    print(f"Documents Assigned:         {metrics['topic_assigned_docs_count']}")
    print("-" * 60)
    print(f"Cross-Source Match Links:   {metrics['cross_source_matches_count']}")
    print(f"  - Accepted Matches:       {metrics['cross_source_accepted_count']}")
    print(f"  - Needs Review:           {metrics['cross_source_review_count']}")
    print(f"  - Unresolved Links:       {metrics['cross_source_unresolved_count']}")
    print("-" * 60)
    print(f"Timeline Snapshots Stored:  {metrics['timeline_snapshots_count']}")
    print("=" * 60 + "\n")
    return 0


def analysis_validate_cmd(args: argparse.Namespace) -> int:
    """Validates structural invariants of Phase 5 analysis tables."""
    storage = SQLiteStorageManager(args.db_path)
    issues = []

    with storage._get_connection() as conn:
        # 1. Invalid embedding dimensions
        bad_dims = conn.execute(
            "SELECT COUNT(*) FROM embedding_records WHERE dimension <= 0;"
        ).fetchone()[0]
        if bad_dims > 0:
            issues.append(f"Found {bad_dims} embedding records with non-positive dimension")

        # 2. Clusters with negative doc counts
        bad_counts = conn.execute(
            "SELECT COUNT(*) FROM topic_clusters WHERE doc_count < 0;"
        ).fetchone()[0]
        if bad_counts > 0:
            issues.append(f"Found {bad_counts} topic clusters with negative doc_count")

        # 3. Cross source matches with invalid similarity scores
        bad_sims = conn.execute(
            "SELECT COUNT(*) FROM cross_source_matches WHERE similarity_score < -1.0 OR similarity_score > 1.0;"
        ).fetchone()[0]
        if bad_sims > 0:
            issues.append(f"Found {bad_sims} cross-source matches with similarity_score outside [-1.0, 1.0]")

    if not issues:
        print("\n[SUCCESS] All Phase 5 analysis structures, vector invariants, and clustering constraints validated perfectly!\n")
        return 0
    else:
        print("\n[WARNING] Invariant issues detected in Phase 5 tables:")
        for iss in issues:
            print(f"  - {iss}")
        print()
        return 1


# -------------------------------------------------------------------------
# Phase 6A: Media Attention vs Performance Analytics Commands
# -------------------------------------------------------------------------
def analytics_preflight_cmd(args: argparse.Namespace) -> int:
    """Runs data eligibility and quality preflight checks."""
    storage = SQLiteStorageManager(args.db_path)
    preflight = AnalyticsPreflight(storage)
    result = preflight.run_preflight(tournament=args.tournament)

    print("\n" + "=" * 70)
    print(f"ANALYTICS PREFLIGHT QUALITY GATE: {result.tournament}")
    print("=" * 70)
    print(f"Overall Eligibility:        {'ELIGIBLE' if result.is_eligible else 'INSUFFICIENT_DATA'}")
    print(f"Quality Status:              {result.status.value}")
    print("-" * 70)
    print("Structured Match Data:")
    print(f"  - Matches Recorded:        {result.matches_count}")
    print(f"  - Deliveries Recorded:     {result.deliveries_count}")
    print(f"  - Batters with Balls:      {result.eligible_batters_count}")
    print(f"  - Bowlers with Balls:      {result.eligible_bowlers_count}")
    print(f"  - Teams Recorded:          {result.eligible_teams_count}")
    print("-" * 70)
    print("Editorial Corpus Data:")
    print(f"  - Articles Ingested:       {result.articles_count}")
    print(f"  - Paragraphs Stored:       {result.paragraphs_count}")
    print(f"  - Commentary Lines:        {result.commentary_count}")
    print("-" * 70)
    print("NLP & Entity Resolution:")
    print(f"  - Total Entity Mentions:   {result.mentions_count}")
    print(f"  - Resolved Mentions:       {result.resolved_mentions_count}")
    print(f"  - Sentiment Baselines:     {result.sentiment_records_count}")
    print("=" * 70)

    if result.warnings:
        print("\nPreflight Quality Warnings:")
        for w in result.warnings:
            print(f"  [!] {w}")

    if result.errors:
        print("\nPreflight Hard Errors:")
        for e in result.errors:
            print(f"  [x] {e}")

    print()
    return 0


def compute_attention_cmd(args: argparse.Namespace) -> int:
    """Computes media attention metrics across the editorial corpus."""
    storage = SQLiteStorageManager(args.db_path)
    calc = MediaAttentionCalculator()

    with storage._get_connection() as conn:
        mentions = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM entity_mentions WHERE resolution_status = 'RESOLVED';"
            ).fetchall()
        ]
        paragraphs = {
            r["paragraph_id"]: dict(r)
            for r in conn.execute("SELECT * FROM article_paragraphs;").fetchall()
        }
        articles = {
            r["article_id"]: dict(r)
            for r in conn.execute("SELECT * FROM articles;").fetchall()
        }
        player_names = {
            r["player_id"]: r["full_name"]
            for r in conn.execute("SELECT player_id, full_name FROM players;").fetchall()
        }
        team_names = {
            r["team_id"]: r["name"]
            for r in conn.execute("SELECT team_id, name FROM teams;").fetchall()
        }
        match_dates = {
            r["match_id"]: r["match_date"]
            for r in conn.execute("SELECT match_id, match_date FROM matches;").fetchall()
        }
        event_alignments = [
            dict(r)
            for r in conn.execute("SELECT * FROM cross_source_matches WHERE status = 'ACCEPTED';").fetchall()
        ]

    if not mentions:
        print("\n[INFO] No resolved entity mentions found in database. Zero attention metrics computed.")
        print("Tip: Ingest articles and run 'process-text' to discover and resolve entity mentions first.\n")
        return 0

    grouped_mentions: dict[str, list[dict]] = {}
    for m in mentions:
        res_id = m.get("resolved_id")
        if res_id:
            grouped_mentions.setdefault(res_id, []).append(m)

    metrics_list = []
    print("\n" + "=" * 90)
    print(f"{'ENTITY NAME':<24} {'TYPE':<8} {'PARAS':<8} {'REACH':<8} {'SOURCES':<8} {'PROMINENCE':<12} {'RAW COMPOSITE'}")
    print("=" * 90)

    for ent_id, ent_mentions in grouped_mentions.items():
        ent_type = "player" if ent_id in player_names else ("team" if ent_id in team_names else "entity")
        ent_name = player_names.get(ent_id, team_names.get(ent_id, ent_id))

        if args.entity and args.entity.lower() not in (ent_id.lower(), ent_name.lower()):
            continue

        metric = calc.compute_for_entity(
            entity_id=ent_id,
            entity_name=ent_name,
            entity_type=ent_type,
            mentions=ent_mentions,
            paragraphs=paragraphs,
            articles=articles,
            event_alignments=event_alignments,
            tournament=args.tournament,
            match_dates=match_dates,
        )
        metrics_list.append(metric)

        if not args.dry_run:
            storage.upsert_attention_metrics(metric)

        print(
            f"{metric.entity_name:<24} {metric.entity_type:<8} {metric.paragraph_count:<8} "
            f"{metric.article_reach:<8} {metric.source_diversity_count:<8} {metric.prominence_score:<12.2f} "
            f"{metric.raw_attention_composite:.2f}"
        )

    print("=" * 90)
    save_str = "Previewed (dry-run)" if args.dry_run else "Persisted to database"
    print(f"Total entities analyzed: {len(metrics_list)} [{save_str}]\n")
    return 0


def compute_performance_cmd(args: argparse.Namespace) -> int:
    """Computes objective cricket performance statistics from canonical match and delivery records."""
    storage = SQLiteStorageManager(args.db_path)
    calc = CricketPerformanceCalculator()

    with storage._get_connection() as conn:
        target_tournament = args.tournament
        check_t = conn.execute("SELECT 1 FROM matches WHERE tournament = ? LIMIT 1;", (args.tournament,)).fetchone()
        if not check_t:
            alias_row = conn.execute(
                """
                SELECT tournament FROM matches 
                WHERE tournament LIKE ? OR ? LIKE ('%' || tournament || '%')
                LIMIT 1;
                """,
                (f"%{args.tournament.replace('2024', '').strip()}%", args.tournament),
            ).fetchone()
            if alias_row:
                target_tournament = alias_row[0]

        deliveries = [
            dict(r)
            for r in conn.execute(
                """
                SELECT d.* FROM deliveries d
                JOIN matches m ON d.match_id = m.match_id
                WHERE m.tournament = ?;
                """,
                (target_tournament,),
            ).fetchall()
        ]
        matches = [
            dict(r)
            for r in conn.execute("SELECT * FROM matches WHERE tournament = ?;", (target_tournament,)).fetchall()
        ]
        player_names = {
            r["player_id"]: r["full_name"]
            for r in conn.execute("SELECT player_id, full_name FROM players;").fetchall()
        }
        team_names = {
            r["team_id"]: r["name"]
            for r in conn.execute("SELECT team_id, name FROM teams;").fetchall()
        }

    if not deliveries and not matches:
        print(f"\n[INFO] No match or delivery records found for tournament '{args.tournament}'. Zero performance metrics computed.")
        print("Tip: Ingest Cricsheet match files to populate structured match data first.\n")
        return 0

    batter_ids = sorted(list(set(d["batter_id"] for d in deliveries)))
    bowler_ids = sorted(list(set(d["bowler_id"] for d in deliveries)))

    computed_metrics = []
    print("\n" + "=" * 95)
    print(f"{'ENTITY NAME':<24} {'ROLE':<12} {'MATCHES':<8} {'RUNS (SR)':<16} {'OVERS (ECON/WKTS)':<20} {'RAW COMPOSITE'}")
    print("=" * 95)

    if args.role in (None, "all", "batter"):
        for pid in batter_ids:
            pname = player_names.get(pid, pid)
            metric = calc.compute_batter_performance(
                player_id=pid,
                player_name=pname,
                deliveries=deliveries,
                matches_played=len(matches),
                tournament=args.tournament,
            )
            computed_metrics.append(metric)
            if not args.dry_run:
                storage.upsert_performance_metrics(metric)
            sr_str = f"{metric.runs_scored} ({metric.strike_rate or 0.0:.1f})"
            print(f"{metric.entity_name:<24} {'batter':<12} {metric.matches_played:<8} {sr_str:<16} {'-':<20} {metric.raw_performance_composite:.2f}")

    if args.role in (None, "all", "bowler"):
        for pid in bowler_ids:
            pname = player_names.get(pid, pid)
            metric = calc.compute_bowler_performance(
                player_id=pid,
                player_name=pname,
                deliveries=deliveries,
                matches_played=len(matches),
                tournament=args.tournament,
            )
            computed_metrics.append(metric)
            if not args.dry_run:
                storage.upsert_performance_metrics(metric)
            bowl_str = f"{metric.overs_bowled:.1f} ov ({metric.bowling_economy or 0.0:.1f} econ, {metric.wickets_taken}w)"
            print(f"{metric.entity_name:<24} {'bowler':<12} {metric.matches_played:<8} {'-':<16} {bowl_str:<20} {metric.raw_performance_composite:.2f}")

    if args.role in (None, "all", "team"):
        distinct_team_ids = set()
        for m in matches:
            distinct_team_ids.add(m["team1_id"])
            distinct_team_ids.add(m["team2_id"])
        for tid in sorted(list(distinct_team_ids)):
            tname = team_names.get(tid, tid)
            metric = calc.compute_team_performance(
                team_id=tid,
                team_name=tname,
                matches=matches,
                tournament=args.tournament,
            )
            computed_metrics.append(metric)
            if not args.dry_run:
                storage.upsert_performance_metrics(metric)
            team_str = f"{metric.team_wins}/{metric.team_matches} wins ({metric.win_percentage or 0.0:.1f}%)"
            print(f"{metric.entity_name:<24} {'team':<12} {metric.matches_played:<8} {team_str:<16} {'-':<20} {metric.raw_performance_composite:.2f}")

    print("=" * 95)
    save_str = "Previewed (dry-run)" if args.dry_run else "Persisted to database"
    print(f"Total performance records: {len(computed_metrics)} [{save_str}]\n")
    return 0


def compute_apdi_cmd(args: argparse.Namespace) -> int:
    """Computes Attention-to-Performance Discrepancy Index (APDI) across role cohorts."""
    storage = SQLiteStorageManager(args.db_path)
    apdi_calc = APDICalculator()
    framing_calc = NarrativeFramingCalculator()

    preflight = AnalyticsPreflight(storage).run_preflight(tournament=args.tournament)
    if not preflight.is_eligible:
        print(f"\n[INSUFFICIENT_DATA] Cannot compute APDI for '{args.tournament}': Data quality preflight failed.")
        print(f"Status: {preflight.status.value}")
        for w in preflight.warnings:
            print(f"  [!] {w}")
        print("Aborting APDI computation without fabricating speculative scores.\n")
        return 0

    all_perf = storage.get_all_performance_metrics(tournament=args.tournament)
    all_att = {r["entity_id"]: r for r in storage.get_all_attention_metrics(tournament=args.tournament)}

    # Auto-cascade: if performance metrics not yet calculated, compute them
    if not all_perf:
        print("[INFO] Performance metrics not found in database. Automatically calculating cricket performance...")
        perf_args = argparse.Namespace(
            db_path=args.db_path,
            config=getattr(args, "config", "config/sources.yaml"),
            tournament=args.tournament,
            role="all",
            dry_run=args.dry_run,
        )
        compute_performance_cmd(perf_args)
        all_perf = storage.get_all_performance_metrics(tournament=args.tournament)

    # Auto-cascade: if attention metrics not yet calculated, compute them
    if not all_att:
        print("[INFO] Attention metrics not found in database. Checking NLP entity mentions...")
        with storage._get_connection() as conn:
            mention_count = conn.execute("SELECT COUNT(*) FROM entity_mentions;").fetchone()[0]
        if mention_count == 0:
            print("[INFO] Processing crawled articles through NLP pipeline...")
            nlp_args = argparse.Namespace(
                db_path=args.db_path,
                config=getattr(args, "config", "config/sources.yaml"),
                limit=None,
                source=None,
                dry_run=args.dry_run,
                all=False,
            )
            process_text_cmd(nlp_args)

        attn_args = argparse.Namespace(
            db_path=args.db_path,
            config=getattr(args, "config", "config/sources.yaml"),
            tournament=args.tournament,
            entity=None,
            dry_run=args.dry_run,
        )
        compute_attention_cmd(attn_args)
        all_att = {r["entity_id"]: r for r in storage.get_all_attention_metrics(tournament=args.tournament)}

    if not all_perf:
        print("\n[INFO] No match or delivery records found to compute performance. Ingest match files with 'run' first.\n")
        return 0

    with storage._get_connection() as conn:
        sentiments = [dict(r) for r in conn.execute("SELECT * FROM sentiment_baselines;").fetchall()]
        paragraphs = {r["paragraph_id"]: dict(r) for r in conn.execute("SELECT * FROM article_paragraphs;").fetchall()}
        articles = {r["article_id"]: dict(r) for r in conn.execute("SELECT * FROM articles;").fetchall()}

    roles_to_run = [args.role] if args.role and args.role != "all" else ["batter", "bowler", "team"]
    all_apdi_records = []
    run_id = f"apdi_run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    print("\n" + "=" * 105)
    print(f"{'RANK':<5} {'ENTITY NAME':<24} {'ROLE':<10} {'NORM ATTN':<12} {'NORM PERF':<12} {'APDI':<10} {'DISCREPANCY':<18} {'STATUS'}")
    print("=" * 105)

    for role_str in roles_to_run:
        role_enum = CohortRole(role_str)
        role_perfs = [p for p in all_perf if p.get("role") == role_str]
        if not role_perfs:
            continue

        cohort_pairs = []
        for p_dict in role_perfs:
            eid = p_dict["entity_id"]
            perf_m = CricketPerformanceMetrics(**p_dict)

            att_dict = all_att.get(eid)
            if att_dict:
                att_m = MediaAttentionMetrics(**att_dict)
            else:
                att_m = MediaAttentionMetrics(
                    metric_id=f"att_{eid}_empty",
                    entity_id=eid,
                    entity_name=perf_m.entity_name,
                    entity_type=perf_m.entity_type,
                    tournament=args.tournament,
                    paragraph_count=0,
                    raw_mention_count=0,
                )

            ent_sentiments = [s for s in sentiments if s.get("target_entity_id") == eid]
            framing_m = framing_calc.compute_framing(eid, ent_sentiments, paragraphs, articles)

            cohort_pairs.append((att_m, perf_m, framing_m))

        records = apdi_calc.compute_cohort_apdi(
            role=role_enum,
            entities_data=cohort_pairs,
            run_id=run_id,
            tournament=args.tournament,
        )
        all_apdi_records.extend(records)

    sorted_records = sorted(
        all_apdi_records,
        key=lambda r: (r.apdi_value is not None, r.apdi_value if r.apdi_value is not None else -999.0),
        reverse=True,
    )

    for rank, r in enumerate(sorted_records, 1):
        norm_att_str = f"{r.normalized_attention_score:.4f}" if r.normalized_attention_score is not None else "N/A"
        norm_perf_str = f"{r.normalized_performance_score:.4f}" if r.normalized_performance_score is not None else "N/A"
        apdi_str = f"{r.apdi_value:+.4f}" if r.apdi_value is not None else "N/A"
        print(
            f"{rank:<5} {r.entity_name:<24} {r.role_cohort.value:<10} {norm_att_str:<12} {norm_perf_str:<12} "
            f"{apdi_str:<10} {r.discrepancy_category.value:<18} {r.evidence_sufficiency_status.value}"
        )

    print("=" * 105)

    if not args.dry_run:
        storage.save_apdi_records(all_apdi_records)
        run_rec = AnalyticsRunRecord(
            run_id=run_id,
            status="completed",
            tournament=args.tournament,
            cohorts_analyzed=roles_to_run,
            entities_processed=len(all_apdi_records),
            valid_apdi_count=sum(1 for r in all_apdi_records if r.apdi_value is not None),
            insufficient_data_count=sum(1 for r in all_apdi_records if r.apdi_value is None),
            completed_at_utc=datetime.now(timezone.utc),
        )
        storage.record_analytics_run(run_rec)
        print(f"APDI run {run_id} persisted to database ({len(all_apdi_records)} records).\n")
        try:
            from scripts.enrich_players_metadata import enrich_all_players
            enrich_all_players()
        except Exception as e:
            logger.debug(f"Player enrichment notice: {e}")
    else:
        print(f"APDI run previewed (dry-run). {len(all_apdi_records)} records computed.\n")

    return 0


def analytics_report_cmd(args: argparse.Namespace) -> int:
    """Displays comprehensive analytical report and entity evidence lineage."""
    storage = SQLiteStorageManager(args.db_path)
    summary = storage.get_analytics_summary(tournament=args.tournament)

    print("\n" + "=" * 70)
    print(f"T20 CRICKET INTELLIGENCE — ANALYTICAL REPORT: {summary['tournament']}")
    print("=" * 70)
    print(f"Stored Attention Metrics:    {summary['attention_metrics_count']}")
    print(f"Stored Performance Metrics:  {summary['performance_metrics_count']}")
    print(f"Total APDI Evaluations:      {summary['apdi_records_count']}")
    print("-" * 70)
    print("Discrepancy Distribution:")
    print(f"  - Over-Attended Entities:  {summary['over_attended_count']}")
    print(f"  - Under-Attended Entities: {summary['under_attended_count']}")
    print(f"  - Balanced Entities:       {summary['balanced_count']}")
    print(f"  - Insufficient Data:       {summary['insufficient_data_count']}")
    print("=" * 70)

    if args.entity:
        records = storage.get_apdi_records(tournament=args.tournament, entity_id=args.entity)
        if not records:
            records = [r for r in storage.get_apdi_records(tournament=args.tournament) if args.entity.lower() in r["entity_name"].lower()]

        if not records:
            print(f"\n[INFO] No APDI records found for entity '{args.entity}'.\n")
            return 0

        rec = records[0]
        print(f"\n>>> Deep Evidence Lineage: {rec['entity_name']} ({rec['role_cohort']}) <<<")
        print(f"  Entity ID:               {rec['entity_id']}")
        print(f"  Comparison Window:       {rec['comparison_window']}")
        print(f"  Discrepancy Category:    {rec['discrepancy_category']}")
        print(f"  Sufficiency Status:      {rec['evidence_sufficiency_status']}")
        print(f"  Raw Attention Composite: {rec['raw_attention_score']:.2f}")
        print(f"  Normalized Attention:    {rec['normalized_attention_score']}")
        print(f"  Raw Performance Score:   {rec['raw_performance_score']:.2f}")
        print(f"  Normalized Performance:  {rec['normalized_performance_score']}")
        print(f"  APDI Value:              {rec['apdi_value']}")
        print(f"  Formula Version:         {rec['formula_version']}")

        print("\n  Sample Size Indicators:")
        for k, v in rec["sample_size_indicators"].items():
            print(f"    - {k}: {v}")

        if rec["data_quality_warnings"]:
            print("\n  Data Quality Warnings:")
            for w in rec["data_quality_warnings"]:
                print(f"    [!] {w}")

        lineage = rec["evidence_lineage"]
        print("\n  Evidence Trace:")
        print(f"    - Contributing Articles:   {lineage.get('contributing_article_ids', [])}")
        print(f"    - Contributing Paragraphs: {lineage.get('contributing_paragraph_ids', [])}")
        print(f"    - Contributing Matches:    {lineage.get('contributing_match_ids', [])}")
        print(f"    - Calculation Notes:       {lineage.get('calculation_notes', '')}")

        framing = rec["framing_breakdown"]
        if framing:
            print("\n  Narrative Framing Analysis:")
            print(f"    - Positive Passages:       {framing.get('positive_count', 0)}")
            print(f"    - Neutral Passages:        {framing.get('neutral_count', 0)}")
            print(f"    - Negative Passages:       {framing.get('negative_count', 0)}")
            print(f"    - Net Framing Score:       {framing.get('net_framing_score', 0.0)}")
            samples = framing.get("supporting_samples", [])
            if samples:
                print("    - Supporting Samples:")
                for s in samples[:3]:
                    print(f"      * [{s.get('sentiment')}] ({s.get('source_domain')}): \"{s.get('text_snippet', '')}\"")

    print()
    return 0


def analytics_validate_cmd(args: argparse.Namespace) -> int:
    """Validates structural invariants of Phase 6A analytics tables."""
    storage = SQLiteStorageManager(args.db_path)
    issues = []

    with storage._get_connection() as conn:
        bad_att = conn.execute(
            """
            SELECT COUNT(*) FROM attention_metrics
            WHERE paragraph_count < 0 OR raw_mention_count < 0 OR article_reach < 0;
            """
        ).fetchone()[0]
        if bad_att > 0:
            issues.append(f"Found {bad_att} attention records with negative counts.")

        bad_perf = conn.execute(
            """
            SELECT COUNT(*) FROM performance_metrics
            WHERE balls_faced < 0 OR legal_balls_bowled < 0 OR runs_scored < 0 OR runs_conceded < 0;
            """
        ).fetchone()[0]
        if bad_perf > 0:
            issues.append(f"Found {bad_perf} performance records with negative balls or runs.")

        bad_norm = conn.execute(
            """
            SELECT COUNT(*) FROM apdi_records
            WHERE (normalized_attention_score IS NOT NULL AND (normalized_attention_score < 0.0 OR normalized_attention_score > 1.0))
               OR (normalized_performance_score IS NOT NULL AND (normalized_performance_score < 0.0 OR normalized_performance_score > 1.0))
               OR (apdi_value IS NOT NULL AND (apdi_value < -1.0 OR apdi_value > 1.0));
            """
        ).fetchone()[0]
        if bad_norm > 0:
            issues.append(f"Found {bad_norm} APDI records with normalized scores outside valid bounds.")

        bad_cat = conn.execute(
            """
            SELECT COUNT(*) FROM apdi_records
            WHERE (apdi_value IS NULL AND discrepancy_category != 'INSUFFICIENT_DATA')
               OR (apdi_value > 0.20 AND discrepancy_category != 'OVER_ATTENDED')
               OR (apdi_value < -0.20 AND discrepancy_category != 'UNDER_ATTENDED')
               OR (apdi_value >= -0.20 AND apdi_value <= 0.20 AND discrepancy_category != 'BALANCED');
            """
        ).fetchone()[0]
        if bad_cat > 0:
            issues.append(f"Found {bad_cat} APDI records with inconsistent discrepancy categories.")

    if not issues:
        print("\n[SUCCESS] All Phase 6A analytics tables, metrics, and APDI invariants validated perfectly!\n")
        return 0
    else:
        print("\n[WARNING] Invariant issues detected in Phase 6A tables:")
        for iss in issues:
            print(f"  - {iss}")
        print()
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

    # Phase 5 commands
    emb_parser = subparsers.add_parser("embed-text", help="Generate semantic embeddings for normalized texts")
    emb_parser.add_argument("--all", action="store_true", help="Embed all eligible normalized texts")
    emb_parser.add_argument("--dry-run", action="store_true", help="Preview embedding counts without persistence")
    emb_parser.add_argument("--model", default="test", help="Embedding model name ('test' or 'sentence-transformers/all-MiniLM-L6-v2')")
    emb_parser.add_argument("--source-type", default=None, help="Filter by source_type ('article_paragraph', 'commentary')")
    emb_parser.add_argument("--limit", type=int, default=None, help="Limit number of items to embed")

    clus_parser = subparsers.add_parser("cluster-topics", help="Cluster text embeddings to discover recurring topics")
    clus_parser.add_argument("--corpus", choices=["editorial", "commentary", "combined"], default="editorial", help="Corpus partition to cluster")
    clus_parser.add_argument("--algorithm", choices=["kmeans", "dbscan"], default="kmeans", help="Clustering algorithm")
    clus_parser.add_argument("--k", type=int, default=5, help="Number of clusters for KMeans")

    eval_parser = subparsers.add_parser("evaluate-topics", help="Evaluate topic clustering quality metrics")
    eval_parser.add_argument("--run-id", default=None, help="Topic run ID to evaluate (defaults to latest)")

    time_parser = subparsers.add_parser("narrative-timeline", help="Construct and view narrative evolution timeline")
    time_parser.add_argument("--match-id", default=None, help="Optional match filter")

    subparsers.add_parser("analysis-stats", help="Show Phase 5 analysis metrics (embeddings, topics, matches)")
    subparsers.add_parser("analysis-validate", help="Validate invariants across Phase 5 analysis tables")

    # Phase 6A commands
    preflight_parser = subparsers.add_parser("analytics-preflight", help="Check data eligibility and quality gates")
    preflight_parser.add_argument("--tournament", default="ICC Men's T20 World Cup", help="Tournament filter")

    attn_parser = subparsers.add_parser("compute-attention", help="Compute media attention metrics across corpus")
    attn_parser.add_argument("--tournament", default="ICC Men's T20 World Cup", help="Tournament filter")
    attn_parser.add_argument("--entity", default=None, help="Optional player or team filter")
    attn_parser.add_argument("--dry-run", action="store_true", help="Preview without database writes")

    perf_parser = subparsers.add_parser("compute-performance", help="Compute objective cricket performance statistics")
    perf_parser.add_argument("--tournament", default="ICC Men's T20 World Cup", help="Tournament filter")
    perf_parser.add_argument("--role", choices=["all", "batter", "bowler", "team"], default="all", help="Role filter")
    perf_parser.add_argument("--dry-run", action="store_true", help="Preview without database writes")

    apdi_parser = subparsers.add_parser("compute-apdi", help="Compute Attention-to-Performance Discrepancy Index")
    apdi_parser.add_argument("--tournament", default="ICC Men's T20 World Cup", help="Tournament filter")
    apdi_parser.add_argument("--role", choices=["all", "batter", "bowler", "team"], default="all", help="Role filter")
    apdi_parser.add_argument("--dry-run", action="store_true", help="Preview without database writes")

    report_parser = subparsers.add_parser("analytics-report", help="Display analytical report and evidence lineage")
    report_parser.add_argument("--tournament", default="ICC Men's T20 World Cup", help="Tournament filter")
    report_parser.add_argument("--entity", default=None, help="Optional entity ID or name for deep evidence trace")

    subparsers.add_parser("analytics-validate", help="Validate structural invariants across Phase 6A tables")

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
        "embed-text": embed_text_cmd,
        "cluster-topics": cluster_topics_cmd,
        "evaluate-topics": evaluate_topics_cmd,
        "narrative-timeline": narrative_timeline_cmd,
        "analysis-stats": analysis_stats_cmd,
        "analysis-validate": analysis_validate_cmd,
        "analytics-preflight": analytics_preflight_cmd,
        "compute-attention": compute_attention_cmd,
        "compute-performance": compute_performance_cmd,
        "compute-apdi": compute_apdi_cmd,
        "analytics-report": analytics_report_cmd,
        "analytics-validate": analytics_validate_cmd,
    }

    cmd_fn = commands.get(args.command)
    if cmd_fn:
        return cmd_fn(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())

