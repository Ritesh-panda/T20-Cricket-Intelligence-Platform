"""Turnkey Database Seeding & Setup Script for T20 Cricket Intelligence Platform.

Executes the complete end-to-end analytical pipeline on a clean clone:
1. Ingest Tier A Cricsheet matches (10 matches, 2,314 deliveries) and Tier B Wikipedia articles (5 articles).
2. Run NLP processing (cleaning, tokenization, NER entity mentions, sentiment baselines).
3. Generate dense semantic embeddings for editorial text.
4. Discover unsupervised topic clusters.
5. Compute objective cricket performance metrics across all batters, bowlers, and teams.
6. Compute media attention metrics and entity prominence scores.
7. Compute Attention-to-Performance Discrepancy Index (APDI) records across cohorts.
8. Enrich all player profiles with verified full names, batting styles, and bowling styles.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.ingest_phase7_corpus import ingest_corpus
from scripts.enrich_players_metadata import enrich_all_players
from src.pipeline.cli import (
    process_text_cmd,
    embed_text_cmd,
    cluster_topics_cmd,
    compute_performance_cmd,
    compute_attention_cmd,
    compute_apdi_cmd,
)
import argparse


def seed():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    start_time = time.time()
    db_path = "data/cricket_intel.db"
    tournament = "ICC Men's T20 World Cup"

    print("\n" + "=" * 80)
    print("INITIALIZING COMPLETE T20 CRICKET INTELLIGENCE PLATFORM DATABASE")
    print(f"Target Database: {db_path} | Tournament: {tournament}")
    print("=" * 80)

    # 1. Ingest raw corpus
    print("\n>>> Step 1/8: Ingesting Cricsheet Matches & Wikipedia Articles...")
    ingest_corpus(db_path=db_path)

    # 2. NLP Pipeline
    print("\n>>> Step 2/8: Running NLP Pipeline (NER & Aspect Sentiment)...")
    nlp_args = argparse.Namespace(db_path=db_path, config="config/sources.yaml", limit=None, source=None, dry_run=False, all=False)
    process_text_cmd(nlp_args)

    # 3. Dense Embeddings
    print("\n>>> Step 3/8: Generating Text Embeddings...")
    emb_args = argparse.Namespace(db_path=db_path, config="config/sources.yaml", limit=None, model="test", source_type=None, dry_run=False)
    embed_text_cmd(emb_args)

    # 4. Topic Clustering
    print("\n>>> Step 4/8: Discovering Topic Clusters...")
    topic_args = argparse.Namespace(db_path=db_path, config="config/sources.yaml", corpus="editorial", algorithm="kmeans", k=5)
    cluster_topics_cmd(topic_args)

    # 5. Cricket Performance
    print("\n>>> Step 5/8: Calculating Objective Cricket Performance...")
    perf_args = argparse.Namespace(db_path=db_path, config="config/sources.yaml", tournament=tournament, role="all", dry_run=False)
    compute_performance_cmd(perf_args)

    # 6. Media Attention
    print("\n>>> Step 6/8: Calculating Media Attention Scores...")
    attn_args = argparse.Namespace(db_path=db_path, config="config/sources.yaml", tournament=tournament, entity=None, dry_run=False)
    compute_attention_cmd(attn_args)

    # 7. APDI Evaluations
    print("\n>>> Step 7/8: Computing Attention-to-Performance Discrepancy Index (APDI)...")
    apdi_args = argparse.Namespace(db_path=db_path, config="config/sources.yaml", tournament=tournament, role="all", dry_run=False)
    compute_apdi_cmd(apdi_args)

    # 8. Enrich Player Profiles
    print("\n>>> Step 8/8: Enriching Full Player Names, Batting & Bowling Styles...")
    enrich_all_players()

    elapsed = time.time() - start_time
    print("\n" + "=" * 80)
    print(f"[SUCCESS] PLATFORM INITIALIZATION COMPLETE in {elapsed:.1f}s!")
    print("=" * 80)
    print("All research data, analytics, topics, and full scorecards are ready.")
    print("Start servers:")
    print("  Backend:  python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload")
    print("  Frontend: cd frontend && npm run dev\n")


if __name__ == "__main__":
    seed()
