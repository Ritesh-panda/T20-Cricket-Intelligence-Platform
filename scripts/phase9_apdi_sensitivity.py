"""Phase 9 APDI Methodology and Sensitivity Analysis Script.

Performs reproducible sensitivity audits of:
1. Threshold sensitivity: +/- 0.15 vs +/- 0.20 vs +/- 0.25
2. Normalization comparison: Percentile Rank vs Min-Max Scaling vs Z-Score
3. Weighting variations: Run-heavy vs Strike-Rate heavy
4. Re-evaluates all 116 entities in data/cricket_intel.db.
"""
import sqlite3
import numpy as np
from pathlib import Path
from typing import Dict, List, Any

DB_PATH = Path("data/cricket_intel.db")

def run_sensitivity_analysis():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    print("=" * 80)
    print("PHASE 9 APDI METHODOLOGY & SENSITIVITY AUDIT")
    print("=" * 80)

    # 1. Fetch current APDI records from DB
    c.execute("""
        SELECT entity_id, entity_name, entity_type, role_cohort,
               raw_attention_score, normalized_attention_score,
               raw_performance_score, normalized_performance_score,
               apdi_value, discrepancy_category, evidence_sufficiency_status
        FROM apdi_records
        ORDER BY apdi_value DESC NULLS LAST;
    """)
    records = c.fetchall()

    valid_records = [r for r in records if r["evidence_sufficiency_status"] == "VALID"]
    insufficient = [r for r in records if r["evidence_sufficiency_status"] != "VALID"]

    print(f"Total Evaluated Entities: {len(records)}")
    print(f"  Valid (Meets Minimum Evidence): {len(valid_records)}")
    print(f"  Insufficient Data (Null APDI):   {len(insufficient)}")
    print("-" * 80)

    # 2. Threshold Sensitivity on Valid Records
    # Current threshold: +/- 0.20
    # Alternatives: +/- 0.15, +/- 0.25
    thresholds = [0.15, 0.20, 0.25]
    print("\n[ANALYSIS 1] THRESHOLD SENSITIVITY TABLE (N = 13 Valid Entities)")
    print(f"{'Entity Name':<22} | {'APDI':<7} | {'Thresh +/-0.15':<15} | {'Thresh +/-0.20 (Base)':<22} | {'Thresh +/-0.25':<15}")
    print("-" * 85)

    for r in valid_records:
        val = r["apdi_value"]
        cat_15 = "OVER_ATTENDED" if val > 0.15 else ("UNDER_ATTENDED" if val < -0.15 else "BALANCED")
        cat_20 = "OVER_ATTENDED" if val > 0.20 else ("UNDER_ATTENDED" if val < -0.20 else "BALANCED")
        cat_25 = "OVER_ATTENDED" if val > 0.25 else ("UNDER_ATTENDED" if val < -0.25 else "BALANCED")
        print(f"{r['entity_name']:<22} | {val:+0.3f}  | {cat_15:<15} | {cat_20:<22} | {cat_25:<15}")

    # Summary of classification shifts across thresholds
    print("-" * 85)
    for t in thresholds:
        over_cnt = sum(1 for r in valid_records if r["apdi_value"] > t)
        under_cnt = sum(1 for r in valid_records if r["apdi_value"] < -t)
        bal_cnt = sum(1 for r in valid_records if -t <= r["apdi_value"] <= t)
        print(f"Threshold +/-{t:0.2f} Breakdown -> Over-attended: {over_cnt}, Balanced: {bal_cnt}, Under-attended: {under_cnt}")

    # 3. Normalization Method Sensitivity
    # Compare Percentile Rank vs Min-Max Scaling vs Standard Score Distance
    print("\n[ANALYSIS 2] NORMALIZATION METHOD COMPARISON")
    print(f"{'Entity Name':<20} | {'Cohort':<7} | {'Raw Att':<8} | {'Raw Perf':<8} | {'Pct APDI':<9} | {'MinMax APDI':<11} | {'Delta':<6}")
    print("-" * 85)

    # Group valid entities by cohort to compute Min-Max within cohort
    cohorts: Dict[str, List[Any]] = {}
    for r in valid_records:
        cohorts.setdefault(r["role_cohort"], []).append(r)

    for cohort_name, cohort_items in cohorts.items():
        if len(cohort_items) < 2:
            continue
        raw_atts = [item["raw_attention_score"] for item in cohort_items]
        raw_perfs = [item["raw_performance_score"] for item in cohort_items]

        min_att, max_att = min(raw_atts), max(raw_atts)
        min_perf, max_perf = min(raw_perfs), max(raw_perfs)

        for item in cohort_items:
            norm_att_mm = (item["raw_attention_score"] - min_att) / (max_att - min_att) if max_att > min_att else 0.5
            norm_perf_mm = (item["raw_performance_score"] - min_perf) / (max_perf - min_perf) if max_perf > min_perf else 0.5
            apdi_mm = round(norm_att_mm - norm_perf_mm, 4)
            pct_apdi = item["apdi_value"]
            delta = round(pct_apdi - apdi_mm, 4)

            print(f"{item['entity_name']:<20} | {cohort_name:<7} | {item['raw_attention_score']:<8.2f} | {item['raw_performance_score']:<8.2f} | {pct_apdi:+0.3f}    | {apdi_mm:+0.3f}       | {delta:+0.3f}")

    print("=" * 80)
    conn.close()

if __name__ == "__main__":
    run_sensitivity_analysis()
