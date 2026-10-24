# Phase 9 Preflight Audit: Repository, Dataset & Baseline Invariant Verification

**Audit Date**: 2026-10-24  
**Branch**: `main`  
**Base Commit**: `2ea6fdc` (`feat(release): complete Phase 8 final integration, research evaluation, and release readiness`)  
**Active Database**: `data/cricket_intel.db` (SQLite, Schema Version 5)  
**Database Backup Created**: `data/cricket_intel_phase9_backup.db` (2,723,840 bytes)  
**Working Tree Status**: Clean

---

## 1. Active Database Identification and Configuration

The platform architecture uses a single unified SQLite database for storage, analytics, API endpoints, and frontend visualization:

- **Active File**: `data/cricket_intel.db`
- **Schema Migrations**: Schema version table `schema_version` contains versions `[2, 3, 4, 5]`. Current version is **5**.
- **CLI / Backend Access**: Configured in [`src/api/config.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/api/config.py) via `DATABASE_PATH = "data/cricket_intel.db"`.
- **Exclusion Verification**: `data/*.db` is tracked by `.gitignore` (line 43). Backup file `data/cricket_intel_phase9_backup.db` is confirmed ignored by git.
- **Stale / Legacy Databases**:
  - `data/cricket_platform.db` (Schema Version 1, 237,568 bytes): confirmed disconnected from all active API routes and ingestion scripts.
  - `data/cricket_intel.db.bak_pre_phase7` (2,723,840 bytes): static archive.

---

## 2. Match Inventory and Provenance Cross-Reconciliation

### 2.1 Cricsheet Source Files vs. Manifest vs. Database

A comprehensive audit was performed comparing the physical files in `data/raw/cricsheet/`, the source register in `data/raw/cricsheet/corpus_manifest.json`, the provenance records in `source_records`, and the canonical match entities in `matches`:

| Raw File / Cricsheet ID | Match Date | Teams | Stage / Context | In Manifest? | In `source_records`? | In `matches` table? | Deliveries in DB |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `1415701.json` | 2024-06-01 | Canada vs USA | Group (Match 1) | YES | YES | `cric_20240601_can_uni` | 226 |
| `1415711.json` | 2024-06-06 | Pakistan vs USA | Group (Match 11, Super Over) | YES | YES | `cric_20240606_pak_uni` | 270 |
| `1415719.json` | 2024-06-09 | India vs Pakistan | Group (Match 19, Low-scoring) | YES | YES | `cric_20240609_ind_pak` | 239 |
| `1415742.json` | 2024-06-19 | West Indies vs England | Super 8 (Match 42) | YES | YES | `cric_20240619_wes_eng` | 222 |
| `1415744.json` | 2024-06-20 | Bangladesh vs Australia | Super 8 (Match 44, DLS Rain) | YES | YES | `cric_20240620_ban_aus` | 126 |
| `1415749.json` | 2024-06-23 | USA vs England | Super 8 (Match 49, Jordan Hat-trick) | YES | YES | `cric_20240623_uni_eng` | 179 |
| `1415750.json` | 2024-06-23 | West Indies vs South Africa | Super 8 (Match 50, DLS Rain) | YES | YES | `cric_20240623_wes_sou` | 204 |
| `1415751.json` | 2024-06-24 | India vs Australia | Super 8 (Match 51, Rohit 92) | YES | YES | `cric_20240624_ind_aus` | 246 |
| `1415754.json` | 2024-06-27 | India vs England | Semi Final 2 (Guyana) | YES | YES | `cric_20240627_ind_eng` | 237 |
| `1415755.json` | 2024-06-29 | India vs South Africa | Final (Bridgetown) | YES | YES | `cric_20240629_ind_sou` | 245 |
| **Totals** | — | **9 Teams** | **10 Matches** | **10 / 10** | **10 / 10** | **10 / 10** | **2,314** |

### 2.2 Forensic Analysis of Match ID Documentation Discrepancy

**Observation**: Earlier phase documentation and exploratory notes occasionally referenced match IDs such as `1415718` (India vs Ireland), `1415752` (India vs Bangladesh), `1415753` (Australia vs Afghanistan / India vs Australia placeholder), and descriptive labels such as "ENG vs NAM" or "USA vs IRE".

**Forensic Investigation & Finding**:
1. During Phase 7 pre-ingestion source selection, an initial exploratory list of 2024 World Cup matches was considered.
2. When the final bounded 10-match corpus was frozen, downloaded, and ingested via [`src/acquisition/cricsheet_adapter.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/src/acquisition/cricsheet_adapter.py), the 10 files actually downloaded and ingested were `1415701, 1415711, 1415719, 1415742, 1415744, 1415749, 1415750, 1415751, 1415754, 1415755`.
3. In `data/raw/cricsheet/corpus_manifest.json`, these exact 10 files are registered with their SHA-256 hashes and sizes.
4. In `data/cricket_intel.db`, the 10 rows in `matches` and 2,314 rows in `deliveries` correspond 1-to-1 with these 10 files.
5. In Phase 8, when `scripts/validate_raw_matches_against_db.py` executed dynamically against `RAW_DIR.glob("*.json")`, all 10 raw JSON files matched the database deliveries and runs with 100% exact parity. However, the markdown summary table in earlier review text had inadvertently copied the tentative draft list from early Phase 7 notes rather than the true manifest list.
6. **Conclusion**: There is zero discrepancy in code, data, or database state. The discrepancy existed solely in historical markdown documentation tables, which are now definitively corrected.

---

## 3. SQL Recomputed Baseline Inventory

All counts recomputed directly using read-only SQL queries against `data/cricket_intel.db`:

```sql
SELECT 'matches', COUNT(*) FROM matches
UNION ALL SELECT 'deliveries', COUNT(*) FROM deliveries
UNION ALL SELECT 'teams', COUNT(*) FROM teams
UNION ALL SELECT 'players', COUNT(*) FROM players
UNION ALL SELECT 'articles', COUNT(*) FROM articles
UNION ALL SELECT 'paragraphs', COUNT(*) FROM article_paragraphs
UNION ALL SELECT 'entity_mentions', COUNT(*) FROM entity_mentions
UNION ALL SELECT 'sentiment_baselines', COUNT(*) FROM sentiment_baselines
UNION ALL SELECT 'embedding_records', COUNT(*) FROM embedding_records
UNION ALL SELECT 'topic_clusters', COUNT(*) FROM topic_clusters
UNION ALL SELECT 'performance_metrics', COUNT(*) FROM performance_metrics
UNION ALL SELECT 'attention_metrics', COUNT(*) FROM attention_metrics
UNION ALL SELECT 'apdi_records', COUNT(*) FROM apdi_records;
```

### Direct SQL Query Results:
- `matches`: **10**
- `deliveries`: **2,314**
- `teams`: **9** (`AFG`, `AUS`, `BAN`, `CAN`, `ENG`, `IND`, `PAK`, `SOU`, `UNI` / USA)
- `players`: **107**
- `articles`: **5**
- `paragraphs`: **314**
- `entity_mentions`: **683**
  - `RESOLVED`: 607 (88.9%)
  - `AMBIGUOUS`: 60 (8.8%)
  - `UNRESOLVED`: 16 (2.3%)
- `sentiment_baselines`: **588**
- `embedding_records`: **314** (384-dimensional dense vectors)
- `topic_clusters`: **3**
- `performance_metrics`: **162**
  - `role = 'batter'`: 93
  - `role = 'bowler'`: 60
  - `role = 'team'`: 9
  - Distinct players evaluated: 107 (46 players appear in both batting and bowling)
- `attention_metrics`: **23** (entities with $\ge 1$ mention in editorial text)
- `apdi_records`: **116** (107 players + 9 teams)
  - `discrepancy_category = 'BALANCED'`, `evidence = 'VALID'`: 7 (`apdi_value` non-null)
  - `discrepancy_category = 'OVER_ATTENDED'`, `evidence = 'VALID'`: 3 (`apdi_value` non-null)
  - `discrepancy_category = 'UNDER_ATTENDED'`, `evidence = 'VALID'`: 3 (`apdi_value` non-null)
  - `discrepancy_category = 'INSUFFICIENT_DATA'`, `evidence = 'INSUFFICIENT_DATA'`: 103 (`apdi_value = NULL`)

---

## 4. Test and Quality Baseline Verification

Preflight execution of test suites:

1. **Python Unit & Integration Suite (`pytest tests/`)**:
   - `104 passed, 7 warnings in 15.73s`
   - Exit code: 0
2. **Frontend Vitest Suite (`npm run test` in `frontend/`)**:
   - `9 passed in 3.42s`
   - Exit code: 0
3. **Frontend TypeScript Check (`npm run typecheck` in `frontend/`)**:
   - `tsc --noEmit`
   - 0 errors
4. **Frontend Production Build (`npm run build` in `frontend/`)**:
   - `vite build` completed in 3.42s
   - Assets generated in `frontend/dist/`
5. **Database Safety Backup**:
   - Confirmed copy at `data/cricket_intel_phase9_backup.db`
   - Unmodified original preserved.

---

## 5. Unresolved Research Questions for Phase 9

1. **Corpus Scope vs Generalizability**: The 5 Wikimedia articles are encyclopedic reference and tournament overview texts. Can we legally expand editorial coverage into genuine match journalism and expert analysis without violating copyright or robots.txt?
2. **APDI Cohort Rigor**: Is comparing all batters in a single percentile rank defensible when sample sizes range from 3 balls to 150 balls?
3. **Threshold Sensitivity**: The $\pm 0.20$ boundaries for `OVER_ATTENDED` / `UNDER_ATTENDED` were established heuristically. How do rankings and classifications shift under $\pm 0.15$ or $\pm 0.25$, or when using $z$-score distance instead of percentile differences?
