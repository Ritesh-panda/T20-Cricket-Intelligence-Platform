"""Phase 8 Database Inventory & Reconciliation Script.

Produces an exact, reproducible inventory of all tables, schema version,
record counts, breakdowns by cohort and status, and traces the APDI discrepancy.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path("data/cricket_intel.db")

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("=" * 80)
    print("PHASE 8 DATABASE INVENTORY AUDIT")
    print("=" * 80)

    # 1. Schema version
    cursor.execute("SELECT version, applied_at_utc FROM schema_version ORDER BY version DESC LIMIT 1;")
    mig = cursor.fetchone()
    print(f"Schema Version: {mig['version'] if mig else 'None'} (applied {mig['applied_at_utc'] if mig else 'N/A'})")

    # 2. Table row counts
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [r["name"] for r in cursor.fetchall() if not r["name"].startswith("sqlite_")]
    print("\n[Table Row Counts]:")
    for t in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {t};")
        cnt = cursor.fetchone()[0]
        print(f"  {t:<30}: {cnt}")

    # 3. Matches, deliveries, teams, players
    cursor.execute("SELECT COUNT(DISTINCT match_id) FROM matches;")
    unique_matches = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT team_id) FROM teams;")
    unique_teams = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT player_id) FROM players;")
    unique_players = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM deliveries;")
    tot_deliveries = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT innings) FROM deliveries;")
    innings_count = cursor.fetchone()[0]

    print("\n[Cricket Core Breakdown]:")
    print(f"  Unique Matches: {unique_matches}")
    print(f"  Total Deliveries: {tot_deliveries}")
    print(f"  Unique Teams: {unique_teams}")
    print(f"  Unique Players: {unique_players}")

    # 4. Editorial & NLP Breakdown
    cursor.execute("SELECT COUNT(DISTINCT article_id) FROM articles;")
    articles = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM article_paragraphs;")
    paragraphs = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM commentary_entries;")
    commentary = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM normalized_texts;")
    norm_texts = cursor.fetchone()[0]
    cursor.execute("SELECT resolution_status, COUNT(*) FROM entity_mentions GROUP BY resolution_status;")
    mentions_by_status = cursor.fetchall()
    cursor.execute("SELECT COUNT(*) FROM sentiment_baselines;")
    sentiments = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM embedding_records;")
    embeddings = cursor.fetchone()[0]

    print("\n[Editorial & NLP Breakdown]:")
    print(f"  Articles: {articles}")
    print(f"  Paragraphs: {paragraphs}")
    print(f"  Commentary Records: {commentary}")
    print(f"  Normalized Texts: {norm_texts}")
    print(f"  Entity Sentiments: {sentiments}")
    print(f"  Embeddings: {embeddings}")
    print("  Entity Mentions by Resolution Status:")
    for r in mentions_by_status:
        print(f"    {r[0]}: {r[1]}")

    # 5. Topic & Narrative Breakdown
    cursor.execute("SELECT COUNT(*) FROM topic_runs;")
    t_runs = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM topic_clusters;")
    t_clusters = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM topic_assignments;")
    t_assigns = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM cross_source_matches;")
    cross_matches = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM event_alignments;")
    event_alignments = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM timeline_snapshots;")
    timelines = cursor.fetchone()[0]

    print("\n[Topics & Narrative Breakdown]:")
    print(f"  Topic Runs: {t_runs}")
    print(f"  Topic Clusters: {t_clusters}")
    print(f"  Topic Assignments: {t_assigns}")
    print(f"  Cross-Source Matches: {cross_matches}")
    print(f"  Event Alignments: {event_alignments}")
    print(f"  Timeline Snapshots: {timelines}")

    # 6. Analytics Breakdown: Performance, Attention, APDI
    cursor.execute("SELECT COUNT(*) FROM analytics_runs;")
    a_runs = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM performance_metrics;")
    perf_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM attention_metrics;")
    attn_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM apdi_records;")
    apdi_count = cursor.fetchone()[0]

    print("\n[Analytics Breakdown]:")
    print(f"  Analytics Runs: {a_runs}")
    print(f"  Performance Metrics Rows: {perf_count}")
    print(f"  Attention Metrics Rows: {attn_count}")
    print(f"  APDI Records Total Rows: {apdi_count}")

    # 7. APDI In-Depth Breakdown & Reconciliation of Discrepancy
    print("\n[APDI Discrepancy Reconciliation]:")
    cursor.execute("SELECT run_id, COUNT(*) FROM apdi_records GROUP BY run_id;")
    apdi_by_run = cursor.fetchall()
    print("  APDI records by run_id:")
    for r in apdi_by_run:
        print(f"    run_id '{r[0]}': {r[1]} rows")

    cursor.execute("""
        SELECT role_cohort, evidence_sufficiency_status, 
               CASE WHEN apdi_value IS NULL THEN 'NULL' ELSE 'NOT NULL' END as apdi_nullity,
               COUNT(*) 
        FROM apdi_records 
        GROUP BY role_cohort, evidence_sufficiency_status, apdi_nullity;
    """)
    cohort_breakdown = cursor.fetchall()
    print("  Breakdown by Cohort, Evidence Status, and APDI Nullity:")
    for r in cohort_breakdown:
        print(f"    cohort={r[0]:<10} | status={r[1]:<18} | apdi_val={r[2]:<8} | count={r[3]}")

    cursor.execute("SELECT COUNT(*) FROM apdi_records WHERE evidence_sufficiency_status = 'VALID';")
    valid_stat_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM apdi_records WHERE evidence_sufficiency_status = 'INSUFFICIENT_DATA';")
    insufficient_stat_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM apdi_records WHERE apdi_value IS NOT NULL;")
    not_null_apdi = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM apdi_records WHERE apdi_value IS NULL;")
    null_apdi = cursor.fetchone()[0]

    print(f"  Total Rows: {apdi_count}")
    print(f"  Rows with evidence_sufficiency_status == 'VALID': {valid_stat_count}")
    print(f"  Rows with evidence_sufficiency_status == 'INSUFFICIENT_DATA': {insufficient_stat_count}")
    print(f"  Rows with apdi_value IS NOT NULL: {not_null_apdi}")
    print(f"  Rows with apdi_value IS NULL: {null_apdi}")
    print(f"  Sum of (VALID + INSUFFICIENT_DATA) = {valid_stat_count + insufficient_stat_count}")

    # Let's see what is stored in performance_metrics vs apdi_records
    cursor.execute("SELECT role, COUNT(*) FROM performance_metrics GROUP BY role;")
    for r in cursor.fetchall():
        print(f"  Performance metrics by role: {r[0]} = {r[1]}")

    cursor.execute("SELECT COUNT(DISTINCT entity_id) FROM performance_metrics WHERE role='batter';")
    nb = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT entity_id) FROM performance_metrics WHERE role='bowler';")
    nbowl = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM (SELECT entity_id FROM performance_metrics WHERE role='batter' INTERSECT SELECT entity_id FROM performance_metrics WHERE role='bowler');")
    nboth = cursor.fetchone()[0]
    print(f"\n[Entity Overlap in Performance Metrics]:")
    print(f"  Batters: {nb}")
    print(f"  Bowlers: {nbowl}")
    print(f"  Players in BOTH Batters and Bowlers: {nboth}")
    print(f"  Total Unique Players across performance_metrics: {nb + nbowl - nboth}")
    print(f"  Total Unique Entities (Players + 9 Teams): {nb + nbowl - nboth + 9}")

    cursor.execute("SELECT role_cohort, COUNT(*) FROM apdi_records GROUP BY role_cohort;")
    for r in cursor.fetchall():
        print(f"  APDI records by cohort: {r[0]} = {r[1]}")

    conn.close()

if __name__ == "__main__":
    main()
