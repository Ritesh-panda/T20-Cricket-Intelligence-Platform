# Phase 9 Release and Research Integrity Checklist

**Evaluation Date**: 2026-10-24  
**Project**: T20 Cricket Intelligence Platform  
**Target Milestone**: Phase 9 — Research Corpus Expansion, Data Provenance & APDI Validity  
**Evaluator**: Lead Research Systems Architect  

---

## 1. Inventory & Preflight Verification

- [x] **Active Database Confirmed**: CLI, API backend, and dashboard all target `data/cricket_intel.db` (SQLite Schema Version 5). Legacy databases (`cricket_platform.db`) are verified disconnected.
- [x] **Match Inventory Reconciliation**: All 10 raw Cricsheet JSON files (`1415701`, `1415711`, `1415719`, `1415742`, `1415744`, `1415749`, `1415750`, `1415751`, `1415754`, `1415755`) reconcile with 100% exact delivery and score parity against the database (2,314 deliveries). Historical documentation notes referencing tentative exploratory matches have been definitively corrected.
- [x] **Database Backup Created**: Verified uncorrupted database copy preserved at `data/cricket_intel_phase9_backup.db` (2,723,840 bytes).
- [x] **Document Deliverable**: [`docs/PHASE_9_PREFLIGHT.md`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/PHASE_9_PREFLIGHT.md) generated and reviewed.

---

## 2. Source Legality, Licensing & Acquisition Protocol

- [x] **Exhaustive Source Matrix**: All 8 current and proposed sources audited across 11 compliance dimensions in [`docs/PHASE_9_SOURCE_LEGALITY_AUDIT.md`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/PHASE_9_SOURCE_LEGALITY_AUDIT.md).
- [x] **Anti-Scraping / Robots Compliance**: ESPNcricinfo (`robots.txt` Disallow), Cricbuzz (proprietary live commentary), and Wisden (Cloudflare challenges) are explicitly categorized as `REQUIRES_PERMISSION` / `RESTRICTED`. Zero unauthorized scraping or bypass mechanisms exist in the codebase.
- [x] **Metadata vs Full-Text Segregation**: BBC Sport Cricket RSS feed is verified and permitted for headlines/excerpts only (`PERMITTED_METADATA_ONLY`); full-text retention is prohibited.
- [x] **Eligible Expansion Identified**: Wikinews (CC BY 2.5) and The Guardian Open Platform API (Developer Tier) audited and prepared for licensed expansion.
- [x] **Source Register Updated**: [`docs/SOURCE_REGISTER.md`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/SOURCE_REGISTER.md) updated with exact hashes, delivery counts, scopes, and legal classifications.

---

## 3. Editorial Corpus & Scope Quality Control

- [x] **Two-Phase Acquisition Protocol**: Discovery and manifest registration operate independently of content acquisition.
- [x] **Timestamp Distinction**: Retrieval timestamp (`retrieval_timestamp_utc`) is strictly segregated from MediaWiki revision timestamp (`published_at_utc`). Unknown timestamps remain `NULL`.
- [x] **Scope Taxonomy Enforced**: Multi-match, tournament overview, squad list, and historical rivalry documents have `linked_match_id = NULL`. Only the Final match report (`2024_Men's_T20_World_Cup_final.html`) links to match `cric_20240629_ind_sou`.
- [x] **Reference vs. Journalism Segregation**: Encyclopedic Wikipedia pages are categorized as `content_type='reference'` and documented as distinct from contemporary sports journalism.
- [x] **Idempotency & Deduplication**: Database insertion enforces deduplication on both canonical URL and body SHA-256 hash.
- [x] **Document Deliverable**: [`docs/PHASE_9_CORPUS_METHOD.md`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/PHASE_9_CORPUS_METHOD.md) generated.

---

## 4. APDI Methodology & Mathematical Sensitivity

- [x] **10 Methodological Dimensions Audited**: Cohort definitions, role separation, sample size variance, composite directions, attention weighting, mention inflation, insufficient data handling, historical stability, and threshold conventions audited in [`docs/PHASE_9_APDI_METHODOLOGY.md`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/PHASE_9_APDI_METHODOLOGY.md).
- [x] **Null APDI Preservation**: All 103 low-sample or zero-mention entities strictly preserve `apdi_value = NULL` and `discrepancy_category = INSUFFICIENT_DATA`. Zero values are never fabricated.
- [x] **Provisional Thresholds**: The $\pm 0.20$ boundaries are formally documented as heuristic and provisional.
- [x] **Empirical Sensitivity Script**: [`scripts/phase9_apdi_sensitivity.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/scripts/phase9_apdi_sensitivity.py) demonstrates that shifting thresholds from $\pm 0.20$ to $\pm 0.15$ shifts 2 borderline teams (`England` and `Australia`) from `BALANCED` to `UNDER_ATTENDED`, while $\pm 0.25$ produces zero shifts.
- [x] **Percentile vs Min-Max Normalization**: Documented mathematical justification for percentile ranking to prevent extreme attention outlier distortion.

---

## 5. NLP, Topic Modeling & Narrative Alignment Protocols

- [x] **NLP Gold Benchmark Validation**: 20-sample gold benchmark evaluated with reproducible confusion matrix: 16 Correctly Resolved (80.0%), 1 Ambiguous (5.0%), 3 Unresolved (15.0%), 0 Wrongly Resolved (0.0% false associations). Honest sample size limitations documented.
- [x] **Topic Modeling Reproduction**: Documented `sentence-transformers/all-MiniLM-L6-v2` embeddings (384 dimensions, L2-normalized) and KMeans ($k=3$, seed 42) producing 3 distinct clusters: History/Rivalry (120 docs), Tactical Encounters (94 docs), and Squad Rosters (100 docs).
- [x] **Absence of Commentary Stream Handled**: With 0 commentary entries in database, event alignment correctly reports `NOT_EVALUABLE` rather than manufacturing artificial links.
- [x] **Document Deliverable**: [`docs/PHASE_9_EVALUATION_PROTOCOL.md`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/docs/PHASE_9_EVALUATION_PROTOCOL.md) generated.

---

## 6. Regression Testing & Build Verification

- [x] **Python Regression Suite**: **112 / 112 passed** in 13.93s (`pytest tests/`). Includes 8 new automated tests in [`tests/test_phase9_validity.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/tests/test_phase9_validity.py).
- [x] **Frontend Vitest Suite**: **9 / 9 passed** in 2.75s (`npm run test` in `frontend/`).
- [x] **Frontend Typecheck**: **0 errors** (`npm run typecheck`).
- [x] **Frontend Production Build**: Clean bundle generated in 3.08s (`npm run build`).

---

## 7. Security, Licensing & Repository Hygiene

- [x] **No Credentials Committed**: Zero API keys or secrets staged or in git history.
- [x] **Git Ignored Artifacts**: Database files (`*.db`), backups, caches (`data/cache/`), raw data (`data/raw/`), and build output (`dist/`) are strictly git-ignored.
- [x] **No Unsupported Claims**: All findings are explicitly qualified as descriptive results from a 10-match research corpus, not causal proofs or universal assertions about sports journalism.

---

## Sign-Off Status: **PHASE 9 ACCEPTED & READY FOR RELEASE**
