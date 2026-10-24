"""Independent Raw JSON to Database Revalidation Script for Phase 8.

Validates all 10 raw Cricsheet JSON source files directly against stored
SQLite database records in data/cricket_intel.db.
"""
import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, List

RAW_DIR = Path("data/raw/cricsheet")
DB_PATH = Path("data/cricket_intel.db")

def parse_raw_source_totals(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Computes ground-truth match and delivery metrics directly from raw JSON."""
    info = raw_data.get("info", {})
    match_type = info.get("match_type", "T20")
    teams = info.get("teams", [])
    outcome = info.get("outcome", {})
    
    innings_list = raw_data.get("innings", [])
    innings_stats = []
    
    total_deliveries = 0
    total_runs_match = 0
    total_wickets_match = 0
    total_wides_match = 0
    total_noballs_match = 0
    total_legal_match = 0
    total_batter_runs_match = 0
    total_extras_match = 0

    for inn_idx, inn in enumerate(innings_list):
        team_name = inn.get("team")
        overs = inn.get("overs", [])
        is_super_over = inn.get("super_over", False)
        
        inn_delivs = 0
        inn_runs = 0
        inn_batter_runs = 0
        inn_extras = 0
        inn_wickets = 0
        inn_legal = 0
        inn_wides = 0
        inn_noballs = 0

        for over_data in overs:
            for deliv in over_data.get("deliveries", []):
                inn_delivs += 1
                total_deliveries += 1
                runs = deliv.get("runs", {})
                b_runs = runs.get("batter", 0)
                e_runs = runs.get("extras", 0)
                tot = runs.get("total", b_runs + e_runs)

                inn_runs += tot
                inn_batter_runs += b_runs
                inn_extras += e_runs

                extras_dict = deliv.get("extras", {})
                wides = extras_dict.get("wides", 0)
                noballs = extras_dict.get("noballs", 0)
                is_legal = (wides == 0 and noballs == 0)

                if is_legal:
                    inn_legal += 1
                    total_legal_match += 1
                if wides > 0:
                    inn_wides += 1
                    total_wides_match += 1
                if noballs > 0:
                    inn_noballs += 1
                    total_noballs_match += 1

                if "wickets" in deliv and deliv["wickets"]:
                    inn_wickets += len(deliv["wickets"])
                    total_wickets_match += len(deliv["wickets"])

        total_runs_match += inn_runs
        total_batter_runs_match += inn_batter_runs
        total_extras_match += inn_extras

        innings_stats.append({
            "innings_index": inn_idx + 1,
            "team": team_name,
            "super_over": is_super_over,
            "deliveries": inn_delivs,
            "legal_balls": inn_legal,
            "runs": inn_runs,
            "batter_runs": inn_batter_runs,
            "extras": inn_extras,
            "wickets": inn_wickets,
            "wides": inn_wides,
            "noballs": inn_noballs,
        })

    return {
        "teams": teams,
        "winner": outcome.get("winner"),
        "result_method": outcome.get("method"), # e.g. D/L
        "result_type": outcome.get("result"), # e.g. tie
        "innings": innings_stats,
        "total_deliveries": total_deliveries,
        "total_runs": total_runs_match,
        "total_batter_runs": total_batter_runs_match,
        "total_extras": total_extras_match,
        "total_wickets": total_wickets_match,
        "total_legal": total_legal_match,
        "total_wides": total_wides_match,
        "total_noballs": total_noballs_match,
    }


def validate_all_matches():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    raw_files = sorted(list(RAW_DIR.glob("*.json")))
    raw_files = [f for f in raw_files if f.name != "corpus_manifest.json"]

    print("=" * 90)
    print("PHASE 8 RAW SOURCE JSON VS DATABASE REVALIDATION (10 MATCHES)")
    print("=" * 90)

    all_passed = True
    total_db_deliveries = 0

    for fpath in raw_files:
        match_num = fpath.stem
        with open(fpath, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        raw_metrics = parse_raw_source_totals(raw_data)

        # Find match in DB via provenance
        cursor.execute("""
            SELECT m.* FROM matches m
            JOIN source_records s ON m.provenance_id = s.provenance_id
            WHERE s.source_identifier LIKE ?;
        """, (f"%{match_num}%",))
        m_row = cursor.fetchone()

        if not m_row:
            print(f"[FAIL] Match {fpath.name} not found in database!")
            all_passed = False
            continue

        db_match_id = m_row["match_id"]

        # Fetch deliveries from DB for this match
        cursor.execute("""
            SELECT innings, COUNT(*) as count,
                   SUM(CASE WHEN is_legal THEN 1 ELSE 0 END) as legal_balls,
                   SUM(batter_runs) as batter_runs,
                   SUM(extra_runs) as extra_runs,
                   SUM(total_runs) as total_runs,
                   SUM(CASE WHEN is_wicket THEN 1 ELSE 0 END) as wickets,
                   SUM(CASE WHEN extra_type = 'wides' THEN 1 ELSE 0 END) as wides,
                   SUM(CASE WHEN extra_type = 'noballs' THEN 1 ELSE 0 END) as noballs
            FROM deliveries
            WHERE match_id = ?
            GROUP BY innings
            ORDER BY innings;
        """, (db_match_id,))
        db_innings = cursor.fetchall()

        # Compare match totals
        cursor.execute("""
            SELECT COUNT(*) as count,
                   SUM(CASE WHEN is_legal THEN 1 ELSE 0 END) as legal_balls,
                   SUM(batter_runs) as batter_runs,
                   SUM(extra_runs) as extra_runs,
                   SUM(total_runs) as total_runs,
                   SUM(CASE WHEN is_wicket THEN 1 ELSE 0 END) as wickets,
                   SUM(CASE WHEN extra_type = 'wides' THEN 1 ELSE 0 END) as wides,
                   SUM(CASE WHEN extra_type = 'noballs' THEN 1 ELSE 0 END) as noballs
            FROM deliveries
            WHERE match_id = ?;
        """, (db_match_id,))
        db_tot = cursor.fetchone()

        total_db_deliveries += db_tot["count"]

        # Verification checks
        deliv_ok = (raw_metrics["total_deliveries"] == db_tot["count"])
        runs_ok = (raw_metrics["total_runs"] == db_tot["total_runs"])
        bat_ok = (raw_metrics["total_batter_runs"] == db_tot["batter_runs"])
        ext_ok = (raw_metrics["total_extras"] == db_tot["extra_runs"])
        wkt_ok = (raw_metrics["total_wickets"] == db_tot["wickets"])
        leg_ok = (raw_metrics["total_legal"] == db_tot["legal_balls"])
        wide_ok = (raw_metrics["total_wides"] == db_tot["wides"])
        nb_ok = (raw_metrics["total_noballs"] == db_tot["noballs"])

        match_ok = all([deliv_ok, runs_ok, bat_ok, ext_ok, wkt_ok, leg_ok, wide_ok, nb_ok])
        status_str = "PASS" if match_ok else "FAIL"
        if not match_ok:
            all_passed = False

        teams_str = f"{raw_metrics['teams'][0]} vs {raw_metrics['teams'][1]}"
        special = ""
        if raw_metrics["result_method"]:
            special += f"[{raw_metrics['result_method']}] "
        if any(inn["super_over"] for inn in raw_metrics["innings"]):
            special += "[Super Over] "

        print(f"[{status_str}] Match {match_num} ({db_match_id}): {teams_str} {special}")
        print(f"       Deliveries: Raw={raw_metrics['total_deliveries']:<4} DB={db_tot['count']:<4} | Runs: Raw={raw_metrics['total_runs']:<4} DB={db_tot['total_runs']:<4}")
        print(f"       Batter Runs: Raw={raw_metrics['total_batter_runs']:<4} DB={db_tot['batter_runs']:<4} | Extras: Raw={raw_metrics['total_extras']:<4} DB={db_tot['extra_runs']:<4}")
        print(f"       Wickets: Raw={raw_metrics['total_wickets']:<4} DB={db_tot['wickets']:<4} | Legal Balls: Raw={raw_metrics['total_legal']:<4} DB={db_tot['legal_balls']:<4}")
        print(f"       Wides: Raw={raw_metrics['total_wides']:<4} DB={db_tot['wides']:<4} | No-balls: Raw={raw_metrics['total_noballs']:<4} DB={db_tot['noballs']:<4}")

    print("-" * 90)
    print(f"Total Matches Checked: {len(raw_files)}")
    print(f"Total Deliveries Verified: {total_db_deliveries} (Expected: 2314)")
    print(f"Overall Structured Verification Status: {'ALL MATCHES PASSED' if all_passed else 'FAILURES DETECTED'}")
    print("=" * 90)

    conn.close()

if __name__ == "__main__":
    validate_all_matches()
